"""
A peer hub.
"""

from uuid import UUID
from common import http
from common import utils
from common.block import APIBlock, Block
from common.pool import Pool
from common.registration import APIRegistration
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
    _registered: bool
    _pool: Pool
    # The following attributes are set after registration
    _hub_name: None | str
    _pre_shared_key: None | bytes

    def __init__(self, client, base_url):
        self._client = client
        self._base_url = base_url
        if self._base_url.endswith("/"):
            self._base_url = self._base_url[:-1]
        self._registered = False
        self._pool = Pool()
        self._hub_name = None
        self._pre_shared_key = None

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
            "pre_shared_key": utils.bytes_to_str(self._pre_shared_key),
            "registered": self._registered,
            "pool": self._pool.to_mgmt(),
        }

    async def register(self) -> None:
        """
        Register this client with the peer hub.
        """
        url = f"{self._base_url}/dske/oob/v1/register-client"
        params = {"client_name": self._client.name}
        registration = await http.get(url, params, APIRegistration)
        self._hub_name = registration.hub_name
        self._pre_shared_key = utils.str_to_bytes(registration.pre_shared_key)
        self._registered = True

    async def unregister(self) -> None:
        """
        Unregister this client from the peer hub.
        """
        # TODO: Implement this

    async def request_psrd(self) -> None:
        """
        Request a block of Pre-Shared Random Data (PSRD) from the peer hub.
        """
        url = f"{self._base_url}/dske/oob/v1/psrd"
        params = {"client_name": self._client.name, "size": _PSRD_BLOCK_SIZE_IN_BYTES}
        api_block = await http.get(url, params, APIBlock)
        block = Block.from_api(api_block)
        self._pool.add_block(block)

    async def post_share(self, share: Share) -> None:
        """
        Post a key share to the peer hub.
        """
        url = f"{self._base_url}/dske/api/v1/key-share"
        api_share = share.to_api(self._client.name)
        await http.post(url, api_obj=api_share)

    async def get_share(self, key_uuid: UUID) -> Share:
        """
        Get a key share from the peer hub.
        """
        url = f"{self._base_url}/dske/api/v1/key-share"
        params = {"client_name": self._client.name, "key_id": str(key_uuid)}
        api_share = await http.get(url, params, APIShare)
        share = Share.from_api(api_share, self._pool)
        return share

    def delete_fully_consumed_blocks(self) -> None:
        """
        Delete fully consumed PSRD blocks from the pool.
        """
        self._pool.delete_fully_consumed_blocks()
