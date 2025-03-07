"""
A DSKE client.
"""

from .peer_hub import PeerHub


class Client:
    """
    A DSKE client.
    """

    _name: str
    _peer_hubs: list[PeerHub]

    def __init__(self, name: str, peer_hub_urls: list[str]):
        self._name = name
        self._peer_hubs = []
        for peer_hub_url in peer_hub_urls:
            peer_hub = PeerHub(peer_hub_url)
            self._peer_hubs.append(peer_hub)

    async def register_all_hubs(self):
        """
        Register all DSKE hubs.
        """
        for peer_hub in self._peer_hubs:
            await peer_hub.register()


    async def unregister_all_hubs(self):
        """
        Unregister all DSKE hubs.
        """
        for peer_hub in self._peer_hubs:
            await peer_hub.unregister()
