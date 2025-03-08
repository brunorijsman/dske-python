"""
A peer DSKE client.
"""

import base64
import uuid

from psrd import PSRDBlock


class PeerClient:
    """
    A peer DSKE client.
    """

    _client_name: str
    _pre_shared_key: bytes
    # TODO: Create classes PSRDBlock and PSRDPool
    _psrds: dict[uuid.UUID, PSRDBlock]  # Indexed by PSRD block UUID

    def __init__(self, client_name: str, pre_shared_key: bytes):
        self._client_name = client_name
        self._pre_shared_key = pre_shared_key
        self._psrds = {}  # TODO: Create class to model a pool of PSRDs

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
            # TODO: Should not report this; include it for now only for debugging
            "pre_shared_key": encoded_pre_shared_key,
        }

    def generate_psrd(self, size: int) -> PSRDBlock:
        """
        Generate a block of PSRD.
        """
        psrd = PSRDBlock.create_random_psrd_block(size)
        assert psrd.uuid not in self._psrds
        self._psrds[psrd.uuid] = psrd
        return psrd
