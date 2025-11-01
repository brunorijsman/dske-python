"""
A peer DSKE client.
"""

from typing import assert_never, List
import fastapi
from common.allocation import Allocation
from common.block import Block
from common.exceptions import InvalidSignatureError
from common.logging import LOGGER
from common.pool import Pool
from common.signature import Signature
from common.signing_key import SigningKey


class PeerClient:
    """
    A peer client of a hub.
    """

    _client_name: str
    _encryptor_names: List[str]
    _local_pool: Pool
    _peer_pool: Pool

    def __init__(self, client_name: str, encryptor_names: List[str]):
        self._client_name = client_name
        self._encryptor_names = encryptor_names
        self._local_pool = Pool(client_name, Pool.Owner.LOCAL)
        self._peer_pool = Pool(client_name, Pool.Owner.PEER)

    @property
    def client_name(self) -> str:
        """
        Get the client name.
        """
        return self._client_name

    @property
    def encryptor_names(self) -> List[str]:
        """
        Get the list of encryptor names registered for this client.
        """
        return self._encryptor_names

    @property
    def local_pool(self) -> Pool:
        """
        Get pool managed by the local hub.
        """
        return self._local_pool

    @property
    def peer_pool(self) -> Pool:
        """
        Get the pool managed by the peer client.
        """
        return self._peer_pool

    def to_mgmt(self):
        """
        Get the management status.
        """
        return {
            "client_name": self._client_name,
            "encryptor_names": self._encryptor_names,
            "local_pool": self._local_pool.to_mgmt(),
            "peer_pool": self._peer_pool.to_mgmt(),
        }

    def create_random_block(self, pool_owner: Pool.Owner, size: int) -> Block:
        """
        Create a block filled ith random data and add it to the specified pool.
        """
        block = Block.new_with_random_data(size)
        match pool_owner:
            case Pool.Owner.LOCAL:
                pool = self._local_pool
            case Pool.Owner.PEER:
                pool = self._peer_pool
            case _:
                assert_never("Invalid pool owner")
        pool.add_block(block)
        return block

    def add_dske_signing_key_header_to_response(self, response: fastapi.Response):
        """
        Add a DSKE-Signing-Key header to a FastAPI response. This header contains the allocation
        and the key value for the authentication key. The signing cannot be done here because we
        need to know the encoded content of the response.
        """
        signing_key = SigningKey.from_pool(self._local_pool)
        signing_key.add_to_headers(response.headers)

    async def check_request_signature(self, raw_request: fastapi.Request):
        """
        Check the signature on a FastAPI request. Raise an exception if the signature is invalid.
        """
        received_signature = Signature.from_headers(raw_request.headers)
        allocation = Allocation.from_enc_str(
            received_signature.signing_key_allocation_enc_str, self._peer_pool
        )
        signing_key = SigningKey(allocation)
        query = raw_request.scope.get("query_string", b"")
        body = await raw_request.body()
        computed_signature = signing_key.sign([query, body])
        signature_ok = received_signature.same_as(computed_signature)
        if not signature_ok:
            # TODO: Give allocation back to pool
            LOGGER.warning(
                f"Invalid signature received from peer client '{self._client_name}'"
            )
            raise InvalidSignatureError()

    def delete_fully_used_blocks(self) -> None:
        """
        Delete fully used PSRD blocks from the pools.
        """
        for pool in (self._local_pool, self._peer_pool):
            pool.delete_fully_used_blocks()
