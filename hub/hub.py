"""
A DSKE hub.
"""

from os import urandom
from uuid import UUID
from .psrd import PSRD
from .peer_client import PeerClient


class Hub:
    """
    A DSKE hub.
    """

    _name: str
    _pre_shared_key_size: int
    _peer_clients: dict[str, PeerClient]  # Indexed by DSKE client name
    # TODO: _psrds are per client, not global for hub
    _psrds: dict[UUID, PSRD]  # Indexed by PSRD UUID

    def __init__(self, name: str, pre_shared_key_size: int):
        self._name = name
        self._pre_shared_key_size = pre_shared_key_size
        self._peer_clients = {}
        self._psrds = {}

    def register_client(self, client_name: str) -> PeerClient:
        """
        Register a DSKE client.
        """
        if client_name in self._peer_clients:
            raise ValueError("DSKE client already peer.")
        pre_shared_key = urandom(self._pre_shared_key_size)
        peer_client = PeerClient(client_name, pre_shared_key)
        self._peer_clients[client_name] = peer_client
        return peer_client

    def create_random_psrd(self, size: int):
        """
        Create a PSRD, containing `size` random bytes.
        """
        psrd = PSRD.create_random_psrd(size)
        assert psrd.uuid not in self._psrds
        self._psrds[psrd.uuid] = psrd
        return psrd
