"""
A peer hub.
"""

import asyncio
from uuid import UUID
from common import exceptions
from common import http
from common.block import APIBlock, Block
from common.pool import Pool
from common.registration import APIRegistrationRequest, APIRegistrationResponse
from common.share import APIShare, Share

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
        self._pool = Pool()
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
            while not await self.attempt_registration():
                await asyncio.sleep(1.0)  # TODO: Introduce constants for this
            while not await self.attempt_request_psrd():
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
        data = APIRegistrationRequest(client_name=self._client.name)
        try:
            registration = await http.put(url, data, APIRegistrationResponse)
        except exceptions.HTTPError:
            print(
                f"Failed to register client {self._client.name} with peer hub at {self._base_url}"
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
        api_share = share.to_api(self._client.name)
        await http.post(
            url=url,
            api_request_obj=api_share,
            api_response_class=None,
            authentication_key_pool=self._pool,
        )

    async def get_share(self, key_uuid: UUID) -> Share:
        """
        Get a key share from the peer hub.
        """
        url = f"{self._base_url}/dske/api/v1/key-share"
        params = {"client_name": self._client.name, "key_id": str(key_uuid)}
        api_share = await http.get(
            url=url,
            params=params,
            api_response_class=APIShare,
            authentication_key_pool=self._pool,
        )
        share = Share.from_api(api_share, self._pool)
        return share

    def delete_fully_consumed_blocks(self) -> None:
        """
        Delete fully consumed PSRD blocks from the pool.
        """
        self._pool.delete_fully_consumed_blocks()
