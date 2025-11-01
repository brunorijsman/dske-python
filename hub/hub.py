"""
A DSKE security hub, or DSKE hub, or just hub for short.
"""

import asyncio
from typing import List
import os
import signal
from uuid import UUID
import fastapi
from common import exceptions
from common import utils
from common.allocation import Allocation
from common.block import Block
from common.encryption_key import EncryptionKey
from common.pool import Pool
from common.share import Share
from common.share_api import APIGetShareResponse, APIPostShareRequest
from common.utils import str_to_bytes, bytes_to_str
from .peer_client import PeerClient


class Hub:
    """
    A DSKE security hub, or DSKE hub, or just hub for short.
    """

    _name: str
    _peer_clients: dict[str, PeerClient]  # Indexed by client name
    _shares: dict[UUID, Share]  # Indexed by key UUID
    _stop_task: asyncio.Task | None

    def __init__(self, name: str):
        self._name = name
        self._peer_clients = {}
        self._shares = {}
        self._stop_task = None

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

    def register_client(
        self, client_name: str, encryptor_names: List[str]
    ) -> PeerClient:
        """
        Register a peer client.
        """
        # We don't check whether the client is already registered (this could happen when the
        # client restarts without unregistering first). The registration of the newly started
        # client will overwrite the existing client.
        peer_client = PeerClient(client_name, encryptor_names)
        self._peer_clients[client_name] = peer_client
        return peer_client

    def generate_block_for_client(
        self, client_name: str, pool_owner_str: str, size: int
    ) -> Block:
        """
        Generate a block of PSRD for a peer client.
        """
        if client_name not in self._peer_clients:
            raise exceptions.ClientNotRegisteredError(client_name)
        peer_client = self._peer_clients[client_name]
        match pool_owner_str.lower():
            case "client":
                pool_owner = Pool.Owner.PEER
            case "hub":
                pool_owner = Pool.Owner.LOCAL
            case _:
                raise exceptions.InvalidPoolOwnerError(pool_owner_str)
        block = peer_client.create_random_block(pool_owner, size)
        return block

    async def store_share_received_from_client(
        self,
        api_post_share_request: APIPostShareRequest,
        raw_request: fastapi.Request,
        headers_temp_response: fastapi.Response,
    ):
        """
        Store a key share posted by a client.
        """
        client_name = api_post_share_request.master_client_name
        if client_name not in self._peer_clients:
            raise exceptions.ClientNotRegisteredError(client_name)
        peer_client = self._peer_clients[client_name]
        await peer_client.check_request_signature(raw_request)
        encryption_key_allocation = Allocation.from_api(
            api_post_share_request.encryption_key_allocation, peer_client.peer_pool
        )
        encryption_key = EncryptionKey.from_allocation(encryption_key_allocation)
        encrypted_share_value = str_to_bytes(
            api_post_share_request.encrypted_share_value
        )
        share_value = encryption_key.decrypt(encrypted_share_value)
        # TODO: Check that master and slave client names match registered client
        share = Share(
            master_sae_id=api_post_share_request.master_sae_id,
            slave_sae_id=api_post_share_request.slave_sae_id,
            user_key_id=UUID(api_post_share_request.user_key_id),
            share_index=api_post_share_request.share_index,
            value=share_value,
        )
        # TODO: Check if the key UUID is already present, and if so, do something sensible
        self._shares[share.user_key_id] = share
        peer_client.add_dske_signing_key_header_to_response(headers_temp_response)
        peer_client.delete_fully_used_blocks()

    async def get_share_requested_by_client(
        self,
        client_name: str,
        key_id_str: str,
        raw_request: fastapi.Request,
        headers_temp_response: fastapi.Response,
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
        await peer_client.check_request_signature(raw_request)
        encryption_key = EncryptionKey.from_pool(peer_client.local_pool, share.size)
        encrypted_share_value = encryption_key.encrypt(share.value)
        response = APIGetShareResponse(
            share_index=share.share_index,
            encryption_key_allocation=encryption_key.allocation.to_api(),
            encrypted_share_value=bytes_to_str(encrypted_share_value),
        )
        peer_client.add_dske_signing_key_header_to_response(headers_temp_response)
        peer_client.delete_fully_used_blocks()
        return response

    def initiate_stop(self):
        """
        Initiate stopping the hub.
        """
        self._stop_task = asyncio.create_task(self._stop_after_delay())

    async def _stop_after_delay(self):
        """
        Stop the hub after a short delay to allow the HTTP response to be sent and to avoid
        TIME_WAIT states on the server.
        """
        await asyncio.sleep(0.5)
        utils.delete_pid_file("hub", self._name)
        os.kill(os.getpid(), signal.SIGTERM)
