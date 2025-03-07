"""
A peer DSKE hub.
"""


class PeerHub:
    """
    A peer DSKE hub.
    """

    _url: str
    _name: str
    _pre_shared_key: str

    def __init__(self, base_url):
        url = base_url
        if not url.endswith("/"):
            url += "/"
        url += "dske/hub/v1"
        self._url = url
        self._name = None
        self._pre_shared_key = None

    async def register(self):
        """
        Register the peer hub.
        """
        print(f"Register peer hub at url {self._url}", flush=True)  ### DEBUG
 

    async def unregister(self):
        """
        Register the peer hub.
        """
        print(f"Unregister peer hub at url {self._url}", flush=True)  ### DEBUG
