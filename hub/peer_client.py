"""
A peer DSKE client.
"""

import base64

from psrd import PSRDBlock, PSRDPool


class PeerClient:
    """
    A peer DSKE client.
    """

    _client_name: str
    _pre_shared_key: bytes
    _psrd_pool: PSRDPool

    def __init__(self, client_name: str, pre_shared_key: bytes):
        self._client_name = client_name
        self._pre_shared_key = pre_shared_key
        self._psrd_pool = PSRDPool()

    @property
    def pre_shared_key(self):
        """
        The pre-shared key.
        """
        return self._pre_shared_key

    def management_status(self):
        """
        Get the management status.
        """
        encoded_pre_shared_key = base64.b64encode(self._pre_shared_key).decode("utf-8")
        return {
            "client_name": self._client_name,
            "pre_shared_key": encoded_pre_shared_key,
            # TODO: XXX Dump the PSRDPool
        }

    def generate_psrd_block(self, size: int) -> PSRDBlock:
        """
        Generate a block of PSRD.
        """
        psrd_block = PSRDBlock.create_random_psrd_block(size)
        self._psrd_pool.add_psrd_block(psrd_block)
        return psrd_block
