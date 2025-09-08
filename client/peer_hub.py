"""
A peer hub.
"""

import asyncio
import sys
from uuid import UUID
from common import exceptions
from common import http
from common.block import APIBlock, Block
from common.encryption_key import EncryptionKey
from common.pool import Allocator, Pool
from common.registration_api import (
    APIPutRegistrationRequest,
    APIPutRegistrationResponse,
)
from common.share import Share
from common.share_api import APIPostShareRequest, APIGetShareResponse
from common.utils import bytes_to_str

# TODO: Decide on logic on how the PSRD block size is decided. Does the client decide? Does
#       the hub decide?
_PSRD_BLOCK_SIZE_IN_BYTES = 1000


class PeerHub:
    """
    A peer hub.
    """

    _client: "Client"  # type: ignore
    _base_url: str
    _startup_task: asyncio.Task | None = None
    _registered: bool
    _pool: Pool
    # The following attributes are set after registration
    _hub_name: None | str

    def __init__(self, client, base_url):
        self._client = client
        self._base_url = base_url
        if self._base_url.endswith("/"):
            self._base_url = self._base_url[:-1]
        self._registered = False
        self._pool = Pool(Allocator.LOCAL)
        self._hub_name = None

    @property
    def pool(self):
        """
        Get the pool for the peer hub.
        """
        return self._pool

    def to_mgmt(self) -> dict:
        """
        Get the management status.
        """
        return {
            "hub_name": self._hub_name,
            "registered": self._registered,
            "pool": self._pool.to_mgmt(),
        }

    def start(self) -> None:
        """
        Create a start task for the peer hub which runs in the background.
        """
        assert self._startup_task is None
        self._startup_task = asyncio.create_task(self.start_task())
        # TODO: Do we need a done_callback? Set start_task to None?

    async def start_task(self) -> None:
        """
        Task for starting the peer hub:
        - Register this client with the hub (periodically retrying if it fails).
        - Request the initial block of Pre-Shared Random Data (PSRD) from the hub (also periodically
          retrying if it fails).
        """
        try:
            print("Starting peer hub...", file=sys.stderr)  # $$$
            print("Registering...", file=sys.stderr)  # $$$
            success = await self.attempt_registration()
            print(f"{success=}", file=sys.stderr)  # $$$
            while not success:
                print("Register failed...", file=sys.stderr)  # $$$
                await asyncio.sleep(1.0)  # TODO: Introduce constants for this
                success = await self.attempt_registration()
                print(f"{success=}", file=sys.stderr)  # $$$
            print("Getting PSRD...", file=sys.stderr)  # $$$
            print("Register success...", file=sys.stderr)  # $$$
            while not await self.attempt_request_psrd():
                print("Get PSRD failed...", file=sys.stderr)  # $$$
                await asyncio.sleep(1.0)
            print("Get PSRD success...", file=sys.stderr)  # $$$
        except asyncio.CancelledError:
            # The task is cancelled when the client is shut down before startup is complete.
            # TODO: Do we need to do anything here? The un-registration is done elsewhere
            pass

    async def attempt_registration(self) -> bool:
        """
        Attempt to register this client with the peer hub. Returns true if successful.
        """
        print("Attempting to register with peer hub...", file=sys.stderr)  # $$$
        url = f"{self._base_url}/dske/oob/v1/registration"
        data = APIPutRegistrationRequest(client_name=self._client.name)
        try:
            registration = await http.put(url, data, APIPutRegistrationResponse)
        except exceptions.HTTPError:
            print(
                f"Failed to register client {self._client.name} with peer hub at {self._base_url}",
                file=sys.stderr,
            )
            return False
        self._hub_name = registration.hub_name
        self._registered = True
        return True

    async def unregister(self) -> None:
        """
        Unregister this client from the peer hub.
        """
        # TODO: Implement this

    async def attempt_request_psrd(self) -> bool:
        """
        Attempt to request a block of Pre-Shared Random Data (PSRD) from the peer hub. Returns true
        if successful.
        """
        print("attempt_request_psrd", file=sys.stderr)  # $$$
        url = f"{self._base_url}/dske/oob/v1/psrd"
        params = {"client_name": self._client.name, "size": _PSRD_BLOCK_SIZE_IN_BYTES}
        try:
            # TODO: Don't attempt to do this until registration succeeded
            api_block = await http.get(url, params, APIBlock)
        except exceptions.HTTPError:
            print(f"Failed to request PSRD block from peer hub at {self._base_url}")
            # TODO: Retry periodically until success
            return False
        block = Block.from_api(api_block)
        self._pool.add_block(block)
        return True

    async def post_share(self, share: Share) -> None:
        """
        Post a key share to the peer hub.
        """
        url = f"{self._base_url}/dske/api/v1/key-share"
        encryption_key = EncryptionKey.from_pool(self._pool, share.size)
        request = APIPostShareRequest(
            client_name=self._client.name,
            user_key_id=str(share.user_key_id),
            share_index=share.share_index,
            encrypted_share_value=bytes_to_str(encryption_key.encrypt(share.value)),
            encryption_key_allocation=encryption_key.allocation.to_api(),
        )
        await http.post(
            url=url,
            api_request_obj=request,
            api_response_class=None,
            authentication_key_pool=self._pool,
        )

    async def get_share(self, key_id: UUID, key_size: int) -> Share:
        """
        Get a key share from the peer hub.
        """
        url = f"{self._base_url}/dske/api/v1/key-share"
        share_size = Share.share_size_for_key_size(key_size)
        encryption_key = EncryptionKey.from_pool(self._pool, share_size)
        params = {
            "client_name": self._client.name,
            "key_id": str(key_id),
            "encryption_key_allocation": encryption_key.allocation.to_param_str(),
        }
        api_get_share_response = await http.get(
            url=url,
            params=params,
            api_response_class=APIGetShareResponse,
            authentication_key_pool=self._pool,
        )
        share = Share(
            user_key_id=api_get_share_response,
            share_index=api_get_share_response.share_index,
            value=api_get_share_response.share_value,
        )
        return share

    def delete_fully_consumed_blocks(self) -> None:
        """
        Delete fully consumed PSRD blocks from the pool.
        """
        self._pool.delete_fully_consumed_blocks()
