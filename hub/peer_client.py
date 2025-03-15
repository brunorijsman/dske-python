"""
A peer DSKE client.
"""

from common import APIShare, Block, bytes_to_str, Pool, Share


class PeerClient:
    """
    A peer DSKE client.
    """

    _client_name: str
    _pre_shared_key: bytes
    _pool: Pool
    _shares: dict[str, Share]  # client name -> Share

    def __init__(self, client_name: str, pre_shared_key: bytes):
        self._client_name = client_name
        self._pre_shared_key = pre_shared_key
        self._pool = Pool()
        self._shares = {}

    @property
    def pre_shared_key(self):
        """
        The pre-shared key.
        """
        return self._pre_shared_key

    def to_mgmt(self):
        """
        Get the management status.
        """
        return {
            "client_name": self._client_name,
            "pre_shared_key": bytes_to_str(self._pre_shared_key),
            "pool": self._pool.to_mgmt(),
        }

    def create_random_block(self, size: int) -> Block:
        """
        Generate a block of PSRD with random data.
        """
        block = Block.create_random_block(size)
        self._pool.add_block(block)
        return block

    def store_share_received_from_client(self, api_share: APIShare):
        """
        Store a key share received from a client.
        """
        share = api_share.from_api()
        # TODO: Check if the key UUID is already present, and if so, do something sensible
        # TODO: Decrypt key value
        # TODO: Check signature
        share = Share.from_api(api_share)
        self._shares[share.key_uuid] = share
