"""
A DSKE client.
"""

from .peer_hub import PeerHub


_MIN_KEY_SIZE_IN_BITS = 1
_MAX_KEY_SIZE_IN_BITS = 100_000  # TODO: Pick a value
_DEFAULT_KEY_SIZE_IN_BITS = 128
_MAX_STORED_KEY_COUNT = 1000  # TODO: What is a sensible value?
_MAX_KEYS_PER_REQUEST = 1  # TODO: Allow more than one


class Client:
    """
    A DSKE client.
    """

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

    def management_status(self):
        """
        Get the management status.
        """
        peer_hubs_status = [
            peer_hub.management_status() for peer_hub in self._peer_hubs
        ]
        return {"client_name": self._client_name, "peer_hubs": peer_hubs_status}

    def etsi_status(self, slave_sae_id: str):
        """
        Get the ETSI QKD 014 V1.1.1 status.
        """
        # See remark about ETSI QKD API in file TODO
        return {
            "source_KME_ID": self._client_name,
            "target_KME_ID": slave_sae_id,
            "master_SAE_ID": self._client_name,
            "slave_SAE_ID": slave_sae_id,
            "key_size": _DEFAULT_KEY_SIZE_IN_BITS,
            "stored_key_count": 25000,  # TODO
            "max_key_count": _MAX_STORED_KEY_COUNT,
            "max_key_per_request": _MAX_KEYS_PER_REQUEST,
            "max_key_size": _MIN_KEY_SIZE_IN_BITS,
            "min_key_size": _MAX_KEY_SIZE_IN_BITS,
            "max_SAE_ID_count": 0,  # TODO: Add support for key multicast
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
