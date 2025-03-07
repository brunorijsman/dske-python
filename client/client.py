"""
A DSKE client.
"""

from .registered_hub import RegisteredHub


class Client:
    """
    A DSKE client.
    """

    _name: str
    _registered_hub: dict[str, RegisteredHub]  # Indexed by DSKE hub name

    def __init__(self, name: str):
        self._name = name
        self._registered_hubs = {}

    def register_hub(self, hub_name: str) -> RegisteredHub:
        """
        Register a DSKE hub.
        """
        print(f"Register hub {hub_name}") ### DEBUG
        if hub_name in self._registered_hub:
            raise ValueError("DSKE hub already registered.")
        # TODO: Receive pre-shared key in registration reply
        pre_shared_key = None
        registered_hub = RegisteredHub(hub_name, pre_shared_key)
        self._registered_hub[hub_name] = registered_hub
        return registered_hub
    
    def register_all_hubs(self):
        """
        Register all DSKE hubs.
        """
        print("Register all hubs") ### DEBUG

    def unregister_all_hubs(self):
        """
        Unregister all DSKE hubs.
        """
        print("Unregister all hubs", flush=True) ### DEBUG
