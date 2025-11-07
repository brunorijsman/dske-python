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
from common.logging import LOGGER
from common.share import Share
from common.share_api import APIGetShareResponse, APIPostShareRequest
from common.owner import Owner
from common.utils import bytes_to_str, key_id_str_to_uuid, str_to_bytes
from .peer_client import PeerClient


class Hub:
    """
    A DSKE security hub, or DSKE hub, or just hub for short.
    """

    _name: str
    _share_timeout_secs: int
    _peer_clients: dict[str, PeerClient]  # Indexed by client name
    _shares: dict[UUID, Share]  # Indexed by key UUID
    _share_timeout_tasks: dict[UUID, asyncio.Task]  # Indexed by key UUID
    _stop_task: asyncio.Task | None

    def __init__(self, name: str, share_timeout_secs: int):
        self._name = name
        self._share_timeout_secs = share_timeout_secs
        self._peer_clients = {}
        self._shares = {}
        self._share_timeout_tasks = {}
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
            "share_timeout_secs": self._share_timeout_secs,
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
        self, client_name: str, owner_str: str, size: int
    ) -> Block:
        """
        Generate a block of PSRD for a peer client.
        """
        peer_client = peer_client = self.lookup_peer_client(client_name)
        owner = Owner.from_str(owner_str, "hub", "client")
        block = peer_client.create_random_block(owner, size)
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
        peer_client = self.lookup_peer_client(client_name)
        await peer_client.check_request_signature(raw_request)
        master_sae_id = api_post_share_request.master_sae_id
        peer_client.check_sae_is_connected(master_sae_id)
        encryption_key_allocation = Allocation.from_api(
            api_post_share_request.encryption_key_allocation, peer_client.peer_pool
        )
        encryption_key = EncryptionKey.from_allocation(encryption_key_allocation)
        encrypted_share_value = str_to_bytes(
            api_post_share_request.encrypted_share_value
        )
        share_value = encryption_key.decrypt(encrypted_share_value)
        share = Share(
            master_sae_id=api_post_share_request.master_sae_id,
            slave_sae_id=api_post_share_request.slave_sae_id,
            user_key_id=UUID(api_post_share_request.user_key_id),
            share_index=api_post_share_request.share_index,
            value=share_value,
        )
        self.store_share(share)
        peer_client.add_dske_signing_key_header_to_response(headers_temp_response)
        peer_client.delete_fully_used_blocks()

    def lookup_peer_client(self, client_name: str) -> PeerClient:
        """
        Lookup a peer client by name.
        """
        if client_name not in self._peer_clients:
            raise exceptions.ClientNotRegisteredError(client_name)
        return self._peer_clients[client_name]

    async def get_share_requested_by_client(
        self,
        client_name: str,
        key_id_str: str,
        master_sae_id: str,
        slave_sae_id: str,
        raw_request: fastapi.Request,
        headers_temp_response: fastapi.Response,
    ) -> APIGetShareResponse:
        """
        Get a key share.
        """
        peer_client = self.lookup_peer_client(client_name)
        peer_client.check_sae_is_connected(slave_sae_id)
        await peer_client.check_request_signature(raw_request)
        key_id = key_id_str_to_uuid(key_id_str)
        share = self.get_share(key_id)
        share.check_master_sae(master_sae_id)
        share.check_slave_sae(slave_sae_id)
        self.delete_share(key_id)
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

    def store_share(self, share: Share):
        """
        Store a share.
        """
        if share.user_key_id in self._shares:
            LOGGER.error(f"Overwriting existing share for key ID {share.user_key_id}")
        self._shares[share.user_key_id] = share
        task = asyncio.create_task(self.delete_share_after_timeout(share.user_key_id))
        self._share_timeout_tasks[share.user_key_id] = task

    def get_share(self, key_id: UUID) -> Share:
        """
        Get a share by key ID. Raise an exception if the share is not found.
        """
        try:
            share = self._shares[key_id]
        except KeyError as exc:
            raise exceptions.UnknownKeyIDError(key_id) from exc
        return share

    def delete_share(self, key_id: UUID):
        """
        Delete a share by key ID.
        """
        if key_id in self._share_timeout_tasks:
            task = self._share_timeout_tasks[key_id]
            task.cancel()
            del self._share_timeout_tasks[key_id]
        if key_id in self._shares:
            del self._shares[key_id]

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

    async def delete_share_after_timeout(self, key_id: UUID):
        """
        Delete a share after the share timeout.
        """
        await asyncio.sleep(self._share_timeout_secs)
        try:
            self.delete_share(key_id)
            LOGGER.info(f"Deleted share for key ID {key_id} after timeout")
        except exceptions.UnknownKeyIDError:
            LOGGER.error(f"Share for key ID {key_id} not found after timeout")
