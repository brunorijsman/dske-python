"""
A DSKE client.
"""

from .peer_hub import PeerHub


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

    def management_status(self):
        """
        Get the management status.
        """
        peer_hubs_status = [peer_hub.management_status() for peer_hub in self._peer_hubs]
        return {"client_name": self._client_name, "peer_hubs": peer_hubs_status}
    

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

    @property
    def name(self):
        """
        Get the client name.
        """
        return self._client_name
