"""
A peer hub.
"""

import asyncio
import sys
from uuid import UUID
from common import exceptions
from common.allocation import Allocation
from common.block import APIBlock, Block
from common.encryption_key import EncryptionKey
from common.pool import Pool
from common.registration_api import (
    APIPutRegistrationRequest,
    APIPutRegistrationResponse,
)
from common.share import Share
from common.share_api import APIPostShareRequest, APIGetShareResponse
from common.utils import bytes_to_str, str_to_bytes
from .http_client import HttpClient

# TODO: Decide on logic on how the PSRD block size is decided. Does the client decide? Does
#       the hub decide?
_PSRD_BLOCK_SIZE_IN_BYTES = 1000


class PeerHub:
    """
    A peer hub.
    """

    _client: "Client"  # type: ignore
    _http_client: HttpClient
    _base_url: str
    _startup_task: asyncio.Task | None = None
    _registered: bool
    _local_pool: Pool
    _peer_pool: Pool
    # The following attributes are set after registration
    _hub_name: None | str

    def __init__(self, client, base_url):
        self._client = client
        self._base_url = base_url
        if self._base_url.endswith("/"):
            self._base_url = self._base_url[:-1]
        self._registered = False
        self._local_pool = Pool(Pool.Owner.LOCAL)
        self._peer_pool = Pool(Pool.Owner.PEER)
        self._hub_name = None
        self._http_client = HttpClient(self._local_pool)

    @property
    def local_pool(self) -> Pool:
        """
        Get the pool managed by the local client.
        """
        return self._local_pool

    @property
    def peer_pool(self) -> Pool:
        """
        Get the pool managed by the peer hub.
        """
        return self._peer_pool

    def to_mgmt(self) -> dict:
        """
        Get the management status.
        """
        return {
            "hub_name": self._hub_name,
            "registered": self._registered,
            "local_pool": self._local_pool.to_mgmt(),
            "peer_pool": self._peer_pool.to_mgmt(),
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
            while not await self.attempt_registration():
                await asyncio.sleep(1.0)  # TODO: Introduce constants for the delay
            for owner in (Pool.Owner.LOCAL, Pool.Owner.PEER):
                while not await self.attempt_request_psrd(owner):
                    await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            # The task is cancelled when the client is shut down before startup is complete.
            # TODO: Do we need to do anything here? The un-registration is done elsewhere
            pass

    async def attempt_registration(self) -> bool:
        """
        Attempt to register this client with the peer hub. Returns true if successful.
        """
        url = f"{self._base_url}/dske/oob/v1/registration"
        data = APIPutRegistrationRequest(client_name=self._client.name)
        try:
            registration = await self._http_client.put(
                url, data, APIPutRegistrationResponse
            )
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

    async def attempt_request_psrd(self, owner: Pool.Owner) -> bool:
        """
        Attempt to request a block of Pre-Shared Random Data (PSRD) from the peer hub. Returns true
        if successful.
        """
        assert self._registered
        url = f"{self._base_url}/dske/oob/v1/psrd"
        match owner:
            case Pool.Owner.LOCAL:
                pool = self._local_pool
                pool_owner_str = "client"
            case Pool.Owner.PEER:
                pool = self._peer_pool
                pool_owner_str = "hub"
        params = {
            "client_name": self._client.name,
            "pool_owner": pool_owner_str,
            "size": _PSRD_BLOCK_SIZE_IN_BYTES,
        }
        try:
            api_block = await self._http_client.get(url, params, APIBlock)
        except exceptions.HTTPError:
            # TODO: Use logging instead of print
            print(f"Failed to request PSRD block from peer hub at {self._base_url}")
            return False
        block = Block.from_api(api_block)
        pool.add_block(block)
        return True

    async def post_share(self, share: Share) -> None:
        """
        Post a key share to the peer hub.
        """
        url = f"{self._base_url}/dske/api/v1/key-share"
        encryption_key = EncryptionKey.from_pool(self._local_pool, share.size)
        request = APIPostShareRequest(
            client_name=self._client.name,
            user_key_id=str(share.user_key_id),
            share_index=share.share_index,
            encryption_key_allocation=encryption_key.allocation.to_api(),
            encrypted_share_value=bytes_to_str(encryption_key.encrypt(share.value)),
        )
        await self._http_client.post(
            url=url,
            api_request_obj=request,
            api_response_class=None,
            authentication=True,
        )

    async def get_share(self, key_id: UUID) -> Share:
        """
        Get a key share from the peer hub.
        """
        url = f"{self._base_url}/dske/api/v1/key-share"
        params = {
            "client_name": self._client.name,
            "key_id": str(key_id),
        }
        response = await self._http_client.get(
            url=url,
            params=params,
            api_response_class=APIGetShareResponse,
            authentication=True,
        )
        encryption_key_allocation = Allocation.from_api(
            response.encryption_key_allocation, self._peer_pool
        )
        encryption_key = EncryptionKey.from_allocation(encryption_key_allocation)
        encrypted_share_value = str_to_bytes(response.encrypted_share_value)
        share_value = encryption_key.decrypt(encrypted_share_value)
        share = Share(
            user_key_id=response, share_index=response.share_index, value=share_value
        )
        return share

    def delete_fully_consumed_blocks(self) -> None:
        """
        Delete fully consumed PSRD blocks from the pool.
        """
        # TODO: Call this more often, not just after scattering a key. Other things can exhaust
        #       blocks too, e.g. decryption keys and signature keys.
        #       Also call it on the hub side for the peer_clients.
        for pool in (self._local_pool, self._peer_pool):
            pool.delete_fully_consumed_blocks()
