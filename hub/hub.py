"""
A DSKE hub.
"""

import os
from uuid import UUID

import key
import psrd

from . import api
from .peer_client import PeerClient


class Hub:
    """
    A DSKE hub.
    """

    _hub_name: str
    _pre_shared_key_size: int
    _peer_clients: dict[str, PeerClient]  # Indexed by DSKE client name
    _user_key_shares: dict[UUID, key.UserKeyShare]  # Indexed by key UUID

    def __init__(self, name: str, pre_shared_key_size: int):
        self._hub_name = name
        self._pre_shared_key_size = pre_shared_key_size
        self._peer_clients = {}
        self._user_key_shares = {}

    def to_mgmt_dict(self):
        """
        Get the management status.
        """
        return {
            "hub_name": self._hub_name,
            "pre_shared_key_size": self._pre_shared_key_size,
            "peer_clients": [
                peer_client.to_mgmt_dict()
                for peer_client in self._peer_clients.values()
            ],
            "user_key_shares": [
                user_key_share.to_mgmt_dict()
                for user_key_share in self._user_key_shares.values()
            ],
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
        psrd_block = peer_client.create_random_psrd_block(size)
        return psrd_block

    def store_key_share_received_from_client(self, api_key_share: api.APIKeyShare):
        """
        Store a key share received from a client.
        """
        user_key_share = api_key_share.to_user_key_share()
        # TODO: Check if the key UUID is already present, and if so, do something sensible
        # TODO: Decrypt key value
        # TODO: Check signature
        self._user_key_shares[user_key_share.user_key_uuid] = user_key_share

    def get_key_share(self, key_id: str) -> api.APIKeyShare:
        """
        Get a key share.
        """
        # TODO: Error handling: key_id is not a valid UUID
        user_key_uuid = UUID(key_id)
        # TODO: Error handling: key_share is not in the store
        user_key_share = self._user_key_shares[user_key_uuid]
        # TODO: Remove it from the store once all responder clients have retrieved it
        return api.APIKeyShare.from_user_key_share(user_key_share)
