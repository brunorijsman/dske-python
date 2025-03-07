"""
A peer DSKE hub.
"""

import base64
import httpx

from psrd import PSRDBlock, PSRDPool

# TODO: Decide on logic on how the PSRD block size is decided. Does the client decide? Does
#       the hub decide?
_PSRD_BLOCK_SIZE_IN_BYTES = 200


class PeerHub:
    """
    A peer DSKE hub.
    """

    _client: "Client"  # type: ignore
    _url: str
    _registered: bool
    _psrd_pool: PSRDPool
    # The following attributes are set after registration
    _name: None | str
    _pre_shared_key: None | bytes

    def __init__(self, client, base_url):
        self._client = client
        url = base_url
        if not url.endswith("/"):
            url += "/"
        url += "dske/hub"
        self._registered = False
        self._psrd_pool = PSRDPool()
        self._url = url
        self._hub_name = None
        self._pre_shared_key = None

    def management_status(self) -> dict:
        """
        Get the management status.
        """
        if self._pre_shared_key is None:
            encoded_pre_shared_key = None
        else:
            encoded_pre_shared_key = base64.b64encode(self._pre_shared_key).decode(
                "utf-8"
            )
        return {
            "hub_name": self._hub_name,
            "pre_shared_key": encoded_pre_shared_key,
            "registered": self._registered,
            "psrd_pool": self._psrd_pool.management_status(),
        }

    async def register(self) -> None:
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
            encoded_pre_shared_key = data["pre_shared_key"]
            pre_shared_key = base64.b64decode(encoded_pre_shared_key.encode("utf-8"))
            self._pre_shared_key = pre_shared_key
            self._registered = True

    async def unregister(self) -> None:
        """
        Register the peer hub.
        """
        # TODO: Implement this

    async def request_psrd(self) -> None:
        """
        Request PSRD from the peer hub.
        """
        async with httpx.AsyncClient() as httpx_client:
            size = _PSRD_BLOCK_SIZE_IN_BYTES
            url = f"{self._url}/oob/v1/psrd?client_name={self._client.name}&size={size}"
            response = await httpx_client.get(url)
            if response.status_code != 200:
                # TODO: Error handling (throw an exception? retry?)
                print(
                    f"Error: {response.status_code=}, {response.content=}", flush=True
                )
                return
            # TODO: Error handling: handle the case that the response does not contain the expected
            #       fields (is that even possible with FastAPI?)
            psrd_block = PSRDBlock.from_protocol_json(response.json())
            self._psrd_pool.add_psrd_block(psrd_block)
