"""
A peer hub.
"""

import asyncio
from uuid import UUID
from common import exceptions
from common.allocation import Allocation
from common.block import APIBlock, Block
from common.encryption_key import EncryptionKey
from common.logging import LOGGER
from common.pool import Pool
from common.registration_api import (
    APIPutRegistrationRequest,
    APIPutRegistrationResponse,
)
from common.share import Share
from common.share_api import APIPostShareRequest, APIGetShareResponse
from common.utils import bytes_to_str, str_to_bytes
from .http_client import HttpClient

# TODO: Make the following configurable.

_START_REQUEST_PSRD_THRESHOLD = 500
"""
Start requesting more PSRD blocks from the hub when the amount of PSRD in the pool falls below this
threshold.
"""

_STOP_REQUEST_PSRD_THRESHOLD = 2000
"""
Stop requesting more PSRD blocks from the hub when the amount of PSRD in the pool rises above or
equal to this threshold.
"""

_GET_PSRD_BLOCK_SIZE = 2000
"""
When requesting more PSRD blocks from the hub, request blocks of this size.
"""

_GET_PSRD_RETRY_DELAY = 1.0
"""
If a get PSRD request to the hub fails, wait this many seconds before retrying.
"""


class PeerHub:
    """
    A peer hub.
    """

    _client: "Client"  # type: ignore
    _http_client: HttpClient
    _base_url: str
    _startup_task: asyncio.Task | None = None
    _request_psrd_task: asyncio.Task | None = None
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
        self._startup_task = None
        self._request_psrd_task = None
        self._registered = False
        self._local_pool = Pool(Pool.Owner.LOCAL)
        self._peer_pool = Pool(Pool.Owner.PEER)
        self._hub_name = None
        self._http_client = HttpClient(self._local_pool, self._peer_pool)

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

    async def start_task(self) -> None:
        """
        Task for starting the peer hub:
        - Register this client with the hub (periodically retrying if it fails).
        - Request the initial block of Pre-Shared Random Data (PSRD) from the hub (also periodically
          retrying if it fails).
        """
        LOGGER.info(f"Begin start task for peer hub at {self._base_url}")
        try:
            while not await self.attempt_registration():
                await asyncio.sleep(_GET_PSRD_RETRY_DELAY)
        except asyncio.CancelledError:
            self._startup_task = None
            LOGGER.info(f"Cancel start task for peer hub at {self._base_url}")
            return
        self.start_request_psrd_task_if_needed()
        self._startup_task = None
        LOGGER.info(f"Finish start task for peer hub at {self._base_url}")

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
            LOGGER.error(
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
        # TODO: Implement this and call it from somewhere

    def start_request_psrd_task_if_needed(self) -> None:
        """
        Start the request PSRD task if needed.
        """
        if self._request_psrd_task is None:
            if self.at_least_one_pool_below_start_threshold():
                self._request_psrd_task = asyncio.create_task(self.request_psrd_task())

    def at_least_one_pool_below_start_threshold(self) -> bool:
        """
        Check if the number of bytes available at least one of the pools is below the threshold
        for starting to get more PSRD from the hub.
        """
        return (
            self._local_pool.bytes_available < _START_REQUEST_PSRD_THRESHOLD
            or self._peer_pool.bytes_available < _START_REQUEST_PSRD_THRESHOLD
        )

    def all_pools_above_stop_threshold(self) -> bool:
        """
        Check if the number of bytes available in all of the pools is above the threshold for
        stopping to get more PSRD from the hub.
        """
        return (
            self._local_pool.bytes_available >= _STOP_REQUEST_PSRD_THRESHOLD
            and self._peer_pool.bytes_available >= _STOP_REQUEST_PSRD_THRESHOLD
        )

    async def request_psrd_task(self) -> None:
        """
        Task for requesting Pre-Shared Random Data (PSRD) from the peer hub. This tasks runs as long
        as the local pool or the peer pool need more PSRD.
        """
        LOGGER.info(f"Begin request PSRD task for peer hub {self._hub_name}")
        try:
            while not self.all_pools_above_stop_threshold():
                need_delay = False
                if self._local_pool.bytes_available < _STOP_REQUEST_PSRD_THRESHOLD:
                    if not await self.attempt_request_psrd(Pool.Owner.LOCAL):
                        need_delay = True
                if self._peer_pool.bytes_available < _STOP_REQUEST_PSRD_THRESHOLD:
                    if not await self.attempt_request_psrd(Pool.Owner.PEER):
                        need_delay = True
                if need_delay:
                    await asyncio.sleep(_GET_PSRD_RETRY_DELAY)
        except asyncio.CancelledError:
            self._request_psrd_task = None
            LOGGER.info(f"Cancel request PSRD task for peer hub {self._hub_name}")
            return
        self._request_psrd_task = None
        LOGGER.info(f"Finish request PSRD task for peer hub {self._hub_name}")

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
            "size": _GET_PSRD_BLOCK_SIZE,
        }
        try:
            api_block = await self._http_client.get(url, params, APIBlock)
        except exceptions.HTTPError:
            LOGGER.error(
                f"Failed to request PSRD block from peer hub at {self._base_url}"
            )
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
