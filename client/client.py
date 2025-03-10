"""
A DSKE client.
"""

import os
import uuid

import common

from .peer_hub import PeerHub


class Client:
    """
    A DSKE client.
    """

    _min_key_size_in_bits = 1
    _max_key_size_in_bits = 100_000  # TODO: Pick a value
    _default_key_size_in_bits = 128
    _max_stored_key_count = 1000  # TODO: What is a sensible value?
    _max_keys_per_request = 1  # TODO: Allow more than one

    _client_name: str
    _peer_hubs: list[PeerHub]

    def __init__(self, name: str, peer_hub_urls: list[str]):
        self._client_name = name
        self._peer_hubs = []
        for peer_hub_url in peer_hub_urls:
            peer_hub = PeerHub(self, peer_hub_url)
            self._peer_hubs.append(peer_hub)

    @property
    def name(self):
        """
        Get the client name.
        """
        return self._client_name

    def to_management_json(self):
        """
        Get the management status.
        """
        peer_hubs_status = [
            peer_hub.to_management_json() for peer_hub in self._peer_hubs
        ]
        return {"client_name": self._client_name, "peer_hubs": peer_hubs_status}

    def etsi_status(self, slave_sae_id: str):
        """
        ETSI QKD 014 V1.1.1 Status API.
        """
        # See remark about ETSI QKD API in file TODO
        return {
            "source_kme_id": self._client_name,
            "target_kme_id": slave_sae_id,
            "master_sae_id": self._client_name,
            "slave_sae_id": slave_sae_id,
            "key_size": self._default_key_size_in_bits,
            "stored_key_count": 25000,  # TODO
            "max_key_count": self._max_stored_key_count,
            "max_key_per_request": self._max_keys_per_request,
            "max_key_size": self._max_key_size_in_bits,
            "min_key_size": self._min_key_size_in_bits,
            "max_sae_id_count": 0,  # TODO: Add support for key multicast
        }

    def etsi_get_key(self, _slave_sae_id: str):
        """
        ETSI QKD 014 V1.1.1 Get Key API.
        """
        # See remark about ETSI QKD API in file TODO
        # TODO: For now, we return a random key UUID and a random key value. We need to implement
        #       the actual key generation using DSKE.
        key_id = uuid.uuid4()
        assert self._default_key_size_in_bits % 8 == 0
        size_in_bytes = self._default_key_size_in_bits // 8
        key_value = os.urandom(size_in_bytes)
        return {
            "keys": {
                "key_ID": key_id,
                "key": common.bytes_to_str(key_value),
            }
        }

    def etsi_get_key_with_key_ids(self, _slave_sae_id: str, key_id: str):
        """
        ETSI QKD 014 V1.1.1 Get Key API.
        """
        # See remark about ETSI QKD API in file TODO
        # TODO: For now, we return a random key UUID and a random key value. We need to implement
        #       the actual key generation using DSKE.
        assert self._default_key_size_in_bits % 8 == 0
        size_in_bytes = self._default_key_size_in_bits // 8
        key_value = os.urandom(size_in_bytes)
        return {
            "keys": {
                "key_ID": key_id,
                "key": common.bytes_to_str(key_value),
            }
        }

    async def register_with_all_peer_hubs(self):
        """
        Register to all peer hubs.
        """
        for peer_hub in self._peer_hubs:
            await peer_hub.register()

    async def unregister_from_all_peer_hubs(self):
        """
        Unregister from all peer hubs.
        """
        for peer_hub in self._peer_hubs:
            await peer_hub.unregister()

    async def request_psrd_from_all_peer_hubs(self):
        """
        Request PSRD from all peer hubs.
        """
        for peer_hub in self._peer_hubs:
            await peer_hub.request_psrd()
