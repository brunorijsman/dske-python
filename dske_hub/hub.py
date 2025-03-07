"""
A DSKE hub.
"""

from os import urandom
from uuid import UUID
from psrd import PSRD
from registered_client import RegisteredClient


class Hub:
    """
    A DSKE hub.
    """
    _name: str
    _pre_shared_key_size: int
    _registered_clients: dict[str, RegisteredClient]  # Indexed by DSKE client name
    # TODO: _psrds are per client, not global for hub
    _psrds: dict[UUID, PSRD]  # Indexed by PSRD UUID

    def __init__(self, name: str, pre_shared_key_size: int):
        self._name = name
        self._pre_shared_key_size = pre_shared_key_size
        self._registered_clients = {}

    def register_client(self, client_name: str) -> RegisteredClient:
        """
        Register a DSKE client.
        """
        if client_name in self._registered_clients:
            raise ValueError("DSKE client already registered.")
        pre_shared_key = urandom(self._pre_shared_key_size)
        registered_client = RegisteredClient(client_name, pre_shared_key)
        self._registered_clients[client_name] = registered_client
        return registered_client

    def create_random_psrd(self, size: int):
        """
        Create a PSRD, containing `size` random bytes.
        """
        psrd = PSRD.create_random_psrd(size)
        assert psrd.uuid not in self._psrds
        self._psrds[psrd.uuid] = psrd
        return psrd
