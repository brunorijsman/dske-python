"""
A peer DSKE client.
"""

import sys
import typing
import fastapi
from common.allocation import Allocation
from common.block import Block
from common.pool import Pool
from common.signature import Signature
from common.signing_key import SigningKey


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
        TODO: better name
        Add a DSKE-Signing-Key header to a FastAPI response. This header contains the allocation
        and the key value for the authentication key. The signing cannot be done here because we
        need to know the encoded content of the response.
        """
        signing_key = SigningKey.from_pool(self._client_pool)
        signing_key.add_to_headers(response.headers)

    async def check_request_signature(self, raw_request: fastapi.Request):
        """
        Check the signature on a FastAPI request. Raise an exception if the signature is invalid.
        """
        received_signature = Signature.from_headers(raw_request.headers)
        print(
            f"check_request_signature: {received_signature=}", file=sys.stderr
        )  # TODO $$$
        print(
            f"check_request_signature: {received_signature.signing_key_allocation_enc_str=}",
            file=sys.stderr,
        )  # TODO $$$
        allocation = Allocation.from_enc_str(
            received_signature.signing_key_allocation_enc_str, self._client_pool
        )
        allocation.mark_allocated()
        print(f"check_request_signature: {allocation=}", file=sys.stderr)  # TODO $$$
        signing_key = SigningKey(allocation)
        print(f"check_request_signature: {signing_key=}", file=sys.stderr)  # TODO $$$
        query = raw_request.scope.get("query_string", b"")
        body = await raw_request.body()
        print(f"{query=}", file=sys.stderr)  # TODO $$$
        print(f"{body=}", file=sys.stderr)  # TODO $$$
        computed_signature = signing_key.sign([query, body])
        print(
            f"check_request_signature: {computed_signature=}", file=sys.stderr
        )  # TODO $$$
        signature_ok = received_signature.same_as(computed_signature)
        print(f"check_request_signature: {signature_ok=}", file=sys.stderr)  # TODO $$$
        if not signature_ok:
            # TODO: Better exception, that causes a 403 forbidden response
            raise ValueError("Invalid signature")
