"""
A peer DSKE client.
"""

import sys
import typing
import fastapi
from common.internal_key import InternalKey
from common.block import Block
from common.pool import Pool
from common.utils import bytes_to_str


class PeerClient:
    """
    A peer client of a hub.
    """

    _client_name: str
    _client_pool: Pool
    _hub_pool: Pool

    def __init__(self, client_name: str):
        self._client_name = client_name
        self._client_pool = Pool(Pool.Owner.CLIENT)
        self._hub_pool = Pool(Pool.Owner.HUB)
        self._shares = {}

    @property
    def client_pool(self) -> Pool:
        """
        Get the client pool.
        """
        return self._client_pool

    @property
    def hub_pool(self) -> Pool:
        """
        Get the hub pool.
        """
        return self._hub_pool

    def to_mgmt(self):
        """
        Get the management status.
        """
        return {
            "client_name": self._client_name,
            "client_pool": self._client_pool.to_mgmt(),
            "hub_pool": self._hub_pool.to_mgmt(),
        }

    def create_random_block(self, pool_owner: Pool.Owner, size: int) -> Block:
        """
        Allocate a block from the specified pool, and fill it with random data.
        """
        block = Block.create_random_block(size)
        match pool_owner:
            case Pool.Owner.CLIENT:
                pool = self._client_pool
            case Pool.Owner.HUB:
                pool = self._hub_pool
            case _:
                typing.assert_never("Invalid pool owner")
        pool.add_block(block)
        return block

    def add_dske_signing_key_header_to_response(self, response: fastapi.Response):
        """
        Add a DSKE-Signing-Key header to a FastAPI response. This header contains the allocation
        and the key value for the authentication key. The signing cannot be done here because we
        need to know the encoded content of the response.
        TODO: Be consistent about calling it signing key or authentication key
        """
        print("add_dske_signing_key_header_to_response", file=sys.stderr)  # TODO $$$
        key = InternalKey.from_pool(self._client_pool, InternalKey.SIGNING_KEY_SIZE)
        allocation_str = key.allocation.to_param_str()
        key_str = bytes_to_str(key.allocation.value)
        header_value = f"{allocation_str};{key_str}"
        response.headers["DSKE-Signing-Key"] = header_value
