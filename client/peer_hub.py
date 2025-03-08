"""
A peer DSKE hub.
"""


import httpx


class PeerHub:
    """
    A peer DSKE hub.
    """

    _client: "Client"  # type: ignore
    _url: str
    _registered: bool
    # The following attributes are set after registration
    _name: None | str
    _pre_shared_key: None | str

    def __init__(self, client, base_url):
        self._client = client
        url = base_url
        if not url.endswith("/"):
            url += "/"
        url += "dske/hub"
        self._registered = False
        self._url = url
        self._hub_name = None
        self._pre_shared_key = None

    def management_status(self):
        """
        Get the management status.
        """
        return {
            "hub_name": self._hub_name,
            # TODO: Should not report this; include it for now only for debugging
            "pre_shared_key": self._pre_shared_key,
            "registered": self._registered,
        }

    async def register(self):
        """
        Register the peer hub.
        """
        async with httpx.AsyncClient() as httpx_client:
            url = f"{self._url}/oob/v1/register-client?client_name={self._client.name}"
            response = await httpx_client.get(url)
            if response.status_code != 200:
                # TODO: Error handling (throw an exception? retry?)
                print(
                    f"Error: {response.status_code=}, {response.content=}", flush=True
                )
                return
            # TODO: Handle the case that the response does not contain the expected fields
            data = response.json()
            self._hub_name = data["hub_name"]
            self._pre_shared_key = data["pre_shared_key"]
            self._registered = True

    async def unregister(self):
        """
        Register the peer hub.
        """
        print(f"Unregister peer hub at url {self._url}", flush=True)  ### DEBUG
        # TODO: Implement this
