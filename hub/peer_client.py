"""
A peer DSKE client.
"""

import common
import psrd


class PeerClient:
    """
    A peer DSKE client.
    """

    _client_name: str
    _pre_shared_key: bytes
    _psrd_pool: psrd.Pool

    def __init__(self, client_name: str, pre_shared_key: bytes):
        self._client_name = client_name
        self._pre_shared_key = pre_shared_key
        self._psrd_pool = psrd.Pool()

    @property
    def pre_shared_key(self):
        """
        The pre-shared key.
        """
        return self._pre_shared_key

    def to_management_json(self):
        """
        Get the management status.
        """
        return {
            "client_name": self._client_name,
            "pre_shared_key": common.bytes_to_str(self._pre_shared_key),
            "psrd_pool": self._psrd_pool.to_management_json(),
        }

    def generate_psrd_block(self, size: int) -> psrd.Block:
        """
        Generate a block of PSRD.
        """
        psrd_block = psrd.Block.create_random_psrd_block(size)
        self._psrd_pool.add_psrd_block(psrd_block)
        return psrd_block
