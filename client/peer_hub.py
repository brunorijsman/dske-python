"""
A peer DSKE hub.
"""

import httpx

import common
import key
import psrd

# TODO: Decide on logic on how the PSRD block size is decided. Does the client decide? Does
#       the hub decide?
_PSRD_BLOCK_SIZE_IN_BYTES = 1000


class PeerHub:
    """
    A peer DSKE hub.
    """

    _client: "Client"  # type: ignore
    _url: str
    _registered: bool
    _psrd_pool: psrd.Pool
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
        self._psrd_pool = psrd.Pool()
        self._url = url
        self._hub_name = None
        self._pre_shared_key = None

    def to_mgmt_dict(self) -> dict:
        """
        Get the management status.
        """
        return {
            "hub_name": self._hub_name,
            "pre_shared_key": common.bytes_to_str(self._pre_shared_key),
            "registered": self._registered,
            "psrd_pool": self._psrd_pool.to_mgmt_dict(),
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
            self._pre_shared_key = common.str_to_bytes(data["pre_shared_key"])
            self._registered = True

    async def unregister(self) -> None:
        """
        Register the peer hub.
        """
        # TODO: Implement this

    async def request_psrd(self) -> None:
        """
        Request a block of Pre-Shared Random Data (PSRD) from the peer hub.
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
            psrd_block = psrd.Block.from_protocol_json(response.json())
            self._psrd_pool.add_psrd_block(psrd_block)

    def allocate_encryption_and_authentication_psrd_keys_for_user_key_share(
        self,
        user_key_share: key.UserKeyShare,
    ):
        """
        Allocate encryption and authentication PSRD keys for a user key share.
        """
        user_key_share.allocate_encryption_and_authentication_psrd_keys_from_pool(
            self._psrd_pool
        )

    async def post_key_share(self, user_key_share: key.UserKeyShare) -> None:
        """
        Post a user key share to the peer hub.
        """
        async with httpx.AsyncClient() as httpx_client:
            ### TODO: Continue from here
            print(f"POST {user_key_share=} to hub {self._hub_name}", flush=True)
            # size = _PSRD_BLOCK_SIZE_IN_BYTES
            # url = f"{self._url}/oob/v1/psrd?client_name={self._client.name}&size={size}"
            # response = await httpx_client.get(url)
            # if response.status_code != 200:
            #     # TODO: Error handling (throw an exception? retry?)
            #     print(
            #         f"Error: {response.status_code=}, {response.content=}", flush=True
            #     )
            #     return
            # # TODO: Error handling: handle the case that the response does not contain the expected
            # #       fields (is that even possible with FastAPI?)
            # psrd_block = psrd.Block.from_protocol_json(response.json())
            # self._psrd_pool.add_psrd_block(psrd_block)
