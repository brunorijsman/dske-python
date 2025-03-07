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

    def register_all_hubs(self):
        """
        Register all DSKE hubs.
        """
        print("Register all hubs")  ### DEBUG

    def register_hub(self, hub_name: str) -> PeerHub:
        """
        Register a DSKE hub.
        """
        print(f"Register hub {hub_name}")  ### DEBUG
        if hub_name in self._peer_hubs:
            raise ValueError("DSKE hub already peer.")
        # TODO: Receive pre-shared key in registration reply
        pre_shared_key = None
        peer_hub = PeerHub(hub_name, pre_shared_key)
        self._peer_hubs[hub_name] = peer_hub
        return peer_hub

    def unregister_all_hubs(self):
        """
        Unregister all DSKE hubs.
        """
        print("Unregister all hubs", flush=True)  ### DEBUG
