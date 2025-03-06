"""
A DSKE hub.
"""

from os import urandom
from uuid import UUID
from dske_client import DSKEClient
from psrd import PSRD


class DSKEHub:
    """
    A DSKE hub.
    """
    _name: str
    _pre_shared_key_size: int
    _dske_clients: dict[str, DSKEClient] # Indexed by DSKE client name
    _psrds: dict[UUID, PSRD] # Indexed by PSRD UUID

    def __init__(self, name: str, pre_shared_key_size: int):
        self._name = name
        self._pre_shared_key_size = pre_shared_key_size
        self._dske_clients = {}

    def register_dske_client(self, dske_client_name: str) -> DSKEClient:
        """
        Register a DSKE client.
        """
        if dske_client_name in self._dske_clients:
            raise ValueError("DSKE client already registered.")
        pre_shared_key = urandom(self._pre_shared_key_size)
        dske_client = DSKEClient(dske_client_name, pre_shared_key)
        self._dske_clients[dske_client_name] = dske_client
        return dske_client

    def create_random_psrd(self, size: int):
        """
        Create a PSRD, containing `size` random bytes.
        """
        psrd = PSRD.create_random_psrd(size)
        assert psrd.uuid not in self._psrds
        self._psrds[psrd.uuid] = psrd
        return psrd
