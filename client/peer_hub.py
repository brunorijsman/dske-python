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

# In real life, the thresholds and the block size defined below would be much larger, perhaps
# gigabytes. For testing purposes, we use much smaller values.

START_REQUEST_PSRD_THRESHOLD = 500
"""
Start requesting more PSRD blocks from the hub when the amount of PSRD in the pool falls below this
threshold.
"""

STOP_REQUEST_PSRD_THRESHOLD = 2000
"""
Stop requesting more PSRD blocks from the hub when the amount of PSRD in the pool rises above or
equal to this threshold.
"""

GET_PSRD_BLOCK_SIZE = 2000
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
    _registered: bool
    _local_pool: Pool
    _peer_pool: Pool
    _register_task: asyncio.Task | None = None
    _local_pool_request_psrd_task: asyncio.Task | None = None
    _peer_pool_request_psrd_task: asyncio.Task | None = None
    _hub_name: None | str  # Set after registration

    def __init__(self, client, base_url):
        self._client = client
        self._base_url = base_url
        if self._base_url.endswith("/"):
            self._base_url = self._base_url[:-1]
        self._registered = False
        hub_name = base_url.split("/")[-1]
        self._local_pool = Pool(hub_name, Pool.Owner.LOCAL)
        self._peer_pool = Pool(hub_name, Pool.Owner.PEER)
        self._register_task = None
        self._local_pool_request_psrd_task = None
        self._peer_pool_request_psrd_task = None
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

    def start_register_task(self) -> None:
        """
        Create a register task, running in the background, for the peer hub.
        """
        assert self._register_task is None
        self._register_task = asyncio.create_task(self.register_task())

    async def register_task(self) -> None:
        """
        Task to register this client with the hub (periodically retrying if it fails). Once
        registered, it starts the request PSRD task.
        """
        task_name = f"register task for peer hub {self._hub_name}"
        LOGGER.info(f"Begin {task_name}")
        try:
            while not await self.attempt_registration():
                await asyncio.sleep(_GET_PSRD_RETRY_DELAY)
        except asyncio.CancelledError:
            self._register_task = None
            LOGGER.info(f"Cancel {task_name}")
        else:
            LOGGER.info(f"Finish {task_name}")
            self.start_request_psrd_task_if_needed()
        finally:
            self._register_task = None

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

    def start_request_psrd_task_if_needed(self) -> None:
        """
        Start request PSRD task(s) if needed.
        """
        if self._local_pool_request_psrd_task is None:
            if self._local_pool.nr_unused_bytes < START_REQUEST_PSRD_THRESHOLD:
                self._local_pool_request_psrd_task = asyncio.create_task(
                    self.request_psrd_task(self._local_pool)
                )
        if self._peer_pool_request_psrd_task is None:
            if self._peer_pool.nr_unused_bytes < START_REQUEST_PSRD_THRESHOLD:
                self._peer_pool_request_psrd_task = asyncio.create_task(
                    self.request_psrd_task(self._peer_pool)
                )

    async def request_psrd_task(self, pool: Pool) -> None:
        """
        Task for requesting Pre-Shared Random Data (PSRD) from the peer hub for a specific pool.
        """
        task_name = f"request PSRD task for peer hub {self._hub_name} and pool owner {pool.owner}"
        LOGGER.info(f"Begin {task_name}")
        try:
            while pool.nr_unused_bytes < STOP_REQUEST_PSRD_THRESHOLD:
                if not await self.attempt_request_psrd(pool):
                    await asyncio.sleep(_GET_PSRD_RETRY_DELAY)
        except asyncio.CancelledError:
            LOGGER.info(f"Cancel {task_name}")
        else:
            LOGGER.info(f"Finish {task_name}")
        finally:
            match pool.owner:
                case Pool.Owner.LOCAL:
                    self._local_pool_request_psrd_task = None
                case Pool.Owner.PEER:
                    self._peer_pool_request_psrd_task = None

    async def attempt_request_psrd(self, pool: Pool) -> bool:
        """
        Attempt to request a block of Pre-Shared Random Data (PSRD) from the peer hub. Returns true
        if successful.
        """
        assert self._registered
        url = f"{self._base_url}/dske/oob/v1/psrd"
        match pool.owner:
            case Pool.Owner.LOCAL:
                pool_owner_str = "client"
            case Pool.Owner.PEER:
                pool_owner_str = "hub"
        params = {
            "client_name": self._client.name,
            "pool_owner": pool_owner_str,
            "size": GET_PSRD_BLOCK_SIZE,
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
        try:
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
        finally:
            self.delete_fully_used_blocks()
            self.start_request_psrd_task_if_needed()

    async def get_share(self, key_id: UUID) -> Share:
        """
        Get a key share from the peer hub.
        """
        try:
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
                user_key_id=response,
                share_index=response.share_index,
                value=share_value,
            )
            return share
        finally:
            self.delete_fully_used_blocks()
            self.start_request_psrd_task_if_needed()

    def delete_fully_used_blocks(self) -> None:
        """
        Delete fully used PSRD blocks from the pools.
        """
        for pool in (self._local_pool, self._peer_pool):
            pool.delete_fully_used_blocks()
