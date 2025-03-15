"""
A peer hub.
"""

from uuid import UUID
import httpx
from common import APIBlock, APIShare, Block, bytes_to_str, Pool, Share, str_to_bytes

# TODO: Decide on logic on how the PSRD block size is decided. Does the client decide? Does
#       the hub decide?
_PSRD_BLOCK_SIZE_IN_BYTES = 1000


class PeerHub:
    """
    A peer hub.
    """

    _client: "Client"  # type: ignore
    _url: str
    _registered: bool
    _pool: Pool
    # The following attributes are set after registration
    _name: None | str
    _pre_shared_key: None | bytes  # TODO: Get rid of pre-shared keys

    def __init__(self, client, base_url):
        self._client = client
        url = base_url
        if not url.endswith("/"):
            url += "/"
        url += "dske/hub"
        self._registered = False
        self._pool = Pool()
        self._url = url
        self._hub_name = None
        self._pre_shared_key = None

    @property
    def pool(self):
        """
        Get the pool for the peer hub.
        """
        return self._pool

    def to_mgmt(self) -> dict:
        """
        Get the management status.
        """
        return {
            "hub_name": self._hub_name,
            "pre_shared_key": bytes_to_str(self._pre_shared_key),
            "registered": self._registered,
            "psrd_pool": self._pool.to_mgmt(),
        }

    async def register(self) -> None:
        """
        Register the peer hub.
        """
        async with httpx.AsyncClient() as httpx_client:
            url = f"{self._url}/oob/v1/register-client"
            get_params = {"client_name": self._client.name}
            response = await httpx_client.get(url, params=get_params)
            if response.status_code != 200:
                # TODO: Error handling (throw an exception? retry?)
                print(
                    f"Error: {response.status_code=}, {response.content=}", flush=True
                )
                return
            # TODO: Handle the case that the response does not contain the expected fields
            data = response.json()
            self._hub_name = data["hub_name"]
            self._pre_shared_key = str_to_bytes(data["pre_shared_key"])
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
            url = f"{self._url}/oob/v1/psrd"
            get_params = {"client_name": self._client.name, "size": size}
            response = await httpx_client.get(url, params=get_params)
            if response.status_code != 200:
                # TODO: Error handling (throw an exception? retry?)
                print(
                    f"Error: {response.status_code=}, {response.content=}", flush=True
                )
                return
            # TODO: Error handling: handle the case that the response does not contain the expected
            #       fields (is that even possible with FastAPI?)
            response_data = response.json()
            api_block = APIBlock.model_validate(response_data)
            block = Block.from_api(api_block)
            self._pool.add_block(block)

    async def post_share(self, share: Share) -> None:
        """
        Post a key share to the peer hub.
        """
        async with httpx.AsyncClient() as httpx_client:
            url = f"{self._url}/api/v1/key-share"
            api_share = share.to_api(self._client.name)
            print(f"{api_share=}", flush=True)  ### DEBUG
            post_data = api_share.model_dump()
            print(f"{url=}", flush=True)  ### DEBUG
            print(f"{post_data=}", flush=True)  ### DEBUG
            response = await httpx_client.post(url, json=post_data)
            if response.status_code != 200:
                # TODO: Error handling (throw an exception? retry?)
                print(
                    f"Error: {response.status_code=}, {response.content=}", flush=True
                )
                return
            # TODO: Error handling: handle the case that the response does not contain the
            # expected fields (is that even possible with FastAPI?)
            response_data = response.json()
            # TODO: For now, there is nothing meaningful in the response data
            print(f"{response_data=}", flush=True)  ### DEBUG

    async def get_share(self, key_uuid: UUID) -> Share:
        """
        Get a key share from the peer hub.
        """
        async with httpx.AsyncClient() as httpx_client:
            url = f"{self._url}/api/v1/key-share"
            get_params = {"client_name": self._client.name, "key_id": str(key_uuid)}
            print(f"{url=}", flush=True)  ### DEBUG
            print(f"{get_params=}", flush=True)  ### DEBUG
            response = await httpx_client.get(url, params=get_params)
            if response.status_code != 200:
                # TODO: Error handling (throw an exception? retry?)
                print(
                    f"Error: {response.status_code=}, {response.content=}", flush=True
                )
                return
            # TODO: Error handling: handle the case that the response does not contain the
            # expected fields (is that even possible with FastAPI?)
            response_data = response.json()
            print(f"{response_data=}", flush=True)  ### DEBUG
            api_share = APIShare.model_validate(response_data)
            print(f"{api_share=}", flush=True)  ### DEBUG
            share = Share.from_api(api_share, self._pool)
            print(f"{share=}", flush=True)  ### DEBUG
            return share

    def delete_fully_consumed_blocks(self) -> None:
        """
        Delete fully consumed PSRD blocks from the pool.
        """
        self._pool.delete_fully_consumed_blocks()
