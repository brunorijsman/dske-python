"""
A DSKE security hub, or DSKE hub, or just hub for short.
"""

from uuid import UUID
from common import exceptions
from common.allocation import Allocation
from common.block import Block
from common.encryption_key import EncryptionKey
from common.share import Share
from common.share_api import APIGetShareResponse, APIPostShareRequest
from common.utils import str_to_bytes
from .peer_client import PeerClient


class Hub:
    """
    A DSKE security hub, or DSKE hub, or just hub for short.
    """

    _name: str
    _peer_clients: dict[str, PeerClient]  # Indexed by client name
    _shares: dict[UUID, Share]  # Indexed by key UUID

    def __init__(self, name: str):
        self._name = name
        self._peer_clients = {}
        self._shares = {}

    @property
    def name(self):
        """
        Get the name.
        """
        return self._name

    def to_mgmt(self):
        """
        Get the management status.
        """
        return {
            "name": self._name,
            "peer_clients": [
                peer_client.to_mgmt() for peer_client in self._peer_clients.values()
            ],
            "shares": [share.to_mgmt() for share in self._shares.values()],
        }

    def register_client(self, client_name: str) -> PeerClient:
        """
        Register a peer client.
        """
        # We don't check whether the client is already registered (this could happen when the
        # client restarts without unregistering first). The registration of the newly started
        # client will overwrite the existing client.
        peer_client = PeerClient(client_name)
        self._peer_clients[client_name] = peer_client
        return peer_client

    def generate_block_for_client(self, client_name: str, size: int) -> Block:
        """
        Generate a block of PSRD for a peer client.
        """
        if client_name not in self._peer_clients:
            raise exceptions.ClientNotRegisteredError(client_name)
        peer_client = self._peer_clients[client_name]
        block = peer_client.create_random_block(size)
        return block

    def store_share_received_from_client(
        self, api_post_share_request: APIPostShareRequest
    ):
        """
        Store a key share posted by a client.
        """
        client_name = api_post_share_request.client_name
        if client_name not in self._peer_clients:
            raise exceptions.ClientNotRegisteredError(client_name)
        peer_client = self._peer_clients[client_name]
        encryption_key_allocation = Allocation.from_api(
            api_post_share_request.encryption_key_allocation, peer_client.pool
        )
        encryption_key = EncryptionKey.from_allocation(encryption_key_allocation)
        encrypted_share_value = str_to_bytes(
            api_post_share_request.encrypted_share_value
        )
        share_value = encryption_key.decrypt(encrypted_share_value)
        share = Share(
            user_key_id=UUID(api_post_share_request.user_key_id),
            share_index=api_post_share_request.share_index,
            value=share_value,
        )
        # TODO: Check if the key UUID is already present, and if so, do something sensible
        self._shares[share.user_key_id] = share

    def get_share_requested_by_client(
        self,
        client_name: str,
        key_id_str: str,
        encryption_key_allocation_str: str,
    ) -> APIGetShareResponse:
        """
        Get a key share.
        """
        try:
            key_id = UUID(key_id_str)
        except ValueError as exc:
            raise exceptions.InvalidKeyIDError(key_id_str) from exc
        # TODO: Error handling: share is not in the store
        try:
            share = self._shares[key_id]
        except KeyError as exc:
            raise exceptions.UnknownKeyIDError(key_id) from exc
        peer_client = self._peer_clients[client_name]
        encryption_key_allocation = Allocation.from_param_str(
            encryption_key_allocation_str, peer_client.pool
        )
        encryption_key = EncryptionKey.from_allocation(encryption_key_allocation)
        encrypted_share_value = encryption_key.encrypt(share.value)
        response = APIGetShareResponse(encrypted_share_value=encrypted_share_value)
        # TODO: Remove it from the store once all responder clients have retrieved it
        #       For now, we don't implement multicast, so we can remove it now (not implemented yet)
        #       Later, when we add multicast, we have to track which responders have and have not
        #       yet gotten the share.
        #       Also, need a time-out to handle the case that some responder never asks for it
        return response
