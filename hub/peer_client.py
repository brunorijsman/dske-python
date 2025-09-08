"""
A peer DSKE client.
"""

from common.block import Block
from common.pool import Allocator, Pool


class PeerClient:
    """
    A peer client of a hub.
    """

    _client_name: str
    _pool: Pool

    def __init__(self, client_name: str):
        self._client_name = client_name
        self._pool = Pool(Allocator.PEER)
        self._shares = {}

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
            "pool": self._pool.to_mgmt(),
        }

    def create_random_block(self, size: int) -> Block:
        """
        Generate a block of PSRD with random data.
        """
        block = Block.create_random_block(size)
        self._pool.add_block(block)
        return block
