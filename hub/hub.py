"""
A DSKE hub.
"""

import os
from copy import deepcopy
from uuid import UUID
from common import (
    APIShare,
    Block,
    ClientAlreadyRegisteredError,
    ClientNotRegisteredError,
    Share,
)
from .peer_client import PeerClient


class Hub:
    """
    A DSKE hub.
    """

    _name: str
    _pre_shared_key_size: int
    _peer_clients: dict[str, PeerClient]  # Indexed by DSKE client name
    _shares: dict[UUID, Share]  # Indexed by key UUID

    def __init__(self, name: str, pre_shared_key_size: int):
        self._name = name
        self._pre_shared_key_size = pre_shared_key_size
        self._peer_clients = {}
        self._shares = {}

    @property
    def name(self):
        """
        Get the hub name.
        """
        return self._name

    def to_mgmt(self):
        """
        Get the management status.
        """
        return {
            "name": self._name,
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
        # TODO: Should we allow an already registered client to be re-registered? This could happen
        #       if a client is restarted, and the hub is not restarted.
        #       For now, we don't allow it.
        if client_name in self._peer_clients:
            raise ClientAlreadyRegisteredError(client_name)
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
            raise ClientNotRegisteredError(client_name)
        peer_client = self._peer_clients[client_name]
        psrd_block = peer_client.create_random_block(size)
        return psrd_block

    def store_share_received_from_client(self, api_share: APIShare):
        """
        Store a key share received from a client.
        """
        client_name = api_share.client_name
        if client_name not in self._peer_clients:
            raise ClientNotRegisteredError(client_name)
        peer_client = self._peer_clients[client_name]
        pool = peer_client.pool
        share = Share.from_api(api_share, pool)
        # TODO: Check if the key UUID is already present, and if so, do something sensible
        # TODO: Decrypt key value
        # TODO: Check signature
        # Verify the signature and decrypt the share.
        share.verify_signature()
        share.decrypt()
        self._shares[share.key_uuid] = share

    def get_share_requested_by_client(self, client_name: str, key_id: str) -> APIShare:
        """
        Get a key share.
        """
        # TODO: The encryption key should be chosen by the client, not the hub, because of possible
        #       race conditions.
        # TODO: Error handling: key_id is not a valid UUID
        key_uuid = UUID(key_id)
        # TODO: Error handling: share is not in the store
        share = self._shares[key_uuid]
        # Make a copy of the share, we don't want to change the unencrypted share in the store.
        share = deepcopy(share)
        # Allocate encryption and authentication keys for the share
        peer_client = self._peer_clients[client_name]
        share.allocate_encryption_and_authentication_keys_from_pool(peer_client.pool)
        # TODO: Error handling. If there was an issue allocating any one of the encryption or
        #       authentication keys, deallocate all of the ones that were allocated, and return
        #       and error to the caller.
        # Encrypt and sign the share
        share.encrypt()
        share.sign()
        # TODO: Remove it from the store once all responder clients have retrieved it
        #       For now, we don't implement multicast, so we can remove it now
        #       Later, when we add multicast, we have to track which responders have and have not
        #       yet gotten the share.
        #       Also, need a time-out to handle the case that some responder never asks for it
        return share.to_api(client_name)
