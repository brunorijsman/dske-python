"""
A DSKE hub.
"""

import os
from uuid import UUID
from common import APIShare, Block, Share
from .peer_client import PeerClient


class Hub:
    """
    A DSKE hub.
    """

    _hub_name: str
    _pre_shared_key_size: int
    _peer_clients: dict[str, PeerClient]  # Indexed by DSKE client name
    _shares: dict[UUID, Share]  # Indexed by key UUID

    def __init__(self, name: str, pre_shared_key_size: int):
        self._hub_name = name
        self._pre_shared_key_size = pre_shared_key_size
        self._peer_clients = {}
        self._shares = {}

    def to_mgmt(self):
        """
        Get the management status.
        """
        return {
            "hub_name": self._hub_name,
            "pre_shared_key_size": self._pre_shared_key_size,
            "peer_clients": [
                peer_client.to_mgmt() for peer_client in self._peer_clients.values()
            ],
            "shares": [share.to_mgmt() for share in self._shares.values()],
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

    def generate_block_for_peer_client(self, client_name: str, size: int) -> Block:
        """
        Generate a block of PSRD for a peer client.
        """
        if client_name not in self._peer_clients:
            # TODO: Not the right kind of exception
            raise ValueError(f"Client {client_name} not registered.")
        peer_client = self._peer_clients[client_name]
        psrd_block = peer_client.create_random_block(size)
        return psrd_block

    def store_share_received_from_client(self, api_share: APIShare):
        """
        Store a key share received from a client.
        """
        client_name = api_share.client_name
        if client_name not in self._peer_clients:
            # TODO: Not the right kind of exception
            raise ValueError(f"Client {client_name} not registered.")
        peer_client = self._peer_clients[client_name]
        peer_client.store_share_received_from_client(api_share)

    def get_api_share(self, key_id: str) -> APIShare:
        """
        Get a key share.
        """
        # TODO: Error handling: key_id is not a valid UUID
        key_uuid = UUID(key_id)
        # TODO: Error handling: share is not in the store
        share = self._shares[key_uuid]
        # TODO: Remove it from the store once all responder clients have retrieved it
        return share.to_api()
