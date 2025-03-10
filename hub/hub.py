"""
A DSKE hub.
"""

import os

import psrd

from .peer_client import PeerClient


class Hub:
    """
    A DSKE hub.
    """

    _hub_name: str
    _pre_shared_key_size: int
    _peer_clients: dict[str, PeerClient]  # Indexed by DSKE client name

    def __init__(self, name: str, pre_shared_key_size: int):
        self._hub_name = name
        self._pre_shared_key_size = pre_shared_key_size
        self._peer_clients = {}

    def to_management_json(self):
        """
        Get the management status.
        """
        peer_clients_status = [
            peer_client.to_management_json()
            for peer_client in self._peer_clients.values()
        ]
        return {
            "hub_name": self._hub_name,
            "pre_shared_key_size": self._pre_shared_key_size,
            "peer_clients": peer_clients_status,
            # TODO: Add PSRDs
        }

    def register_peer_client(self, client_name: str) -> PeerClient:
        """
        Register a peer client.
        """
        if client_name in self._peer_clients:
            # TODO: Not the right kind of exception
            raise ValueError(f"Client {client_name} already registered.")
        # TODO: Choose pre-shared key in PeerClient constructor?
        pre_shared_key = os.urandom(self._pre_shared_key_size)
        peer_client = PeerClient(client_name, pre_shared_key)
        self._peer_clients[client_name] = peer_client
        return peer_client

    def generate_psrd_block_for_peer_client(
        self, client_name: str, size: int
    ) -> psrd.Block:
        """
        Generate a block of PSRD for a peer client.
        """
        if client_name not in self._peer_clients:
            # TODO: Not the right kind of exception
            raise ValueError(f"Client {client_name} not registered.")
        peer_client = self._peer_clients[client_name]
        psrd_block = peer_client.generate_psrd_block(size)
        return psrd_block
