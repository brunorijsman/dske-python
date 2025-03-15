"""
A peer DSKE client.
"""

from common import Block, bytes_to_str, Pool


class PeerClient:
    """
    A peer DSKE client.
    """

    _client_name: str
    _pre_shared_key: bytes
    _pool: Pool

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

    @property
    def pool(self):
        """
        Get the pool.
        """
        return self._pool

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
