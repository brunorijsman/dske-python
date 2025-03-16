"""
Exceptions.
"""

from fastapi import HTTPException
from httpx import codes


class DSKEException(HTTPException):
    """
    Base class for all Distributed Symmetric Key Exchange (DSKE) exceptions. Records the type and
    the name of the node that raised the exception, and optionally also the type and the name of
    the peer node.
    """

    def __init__(
        self,
        status_code: int,
        detail: str,
        node_type: str,
        node_name: str,
        peer_type: str | None = None,
        peer_name: str | None = None,
    ):
        prefix = f"{node_type} {node_name}"
        if peer_type is not None:
            assert peer_name is not None
            prefix += f" -> {peer_type} {peer_name}"
        detail = f"{prefix}: {detail}"
        super().__init__(status_code, detail=detail)


class OutOfPreSharedRandomDataException(DSKEException):
    """
    Out of Pre-Shared Random Data (PSRD). We tried to allocated some pre-shared random data from
    a pool, but the pool did not contain enough free data to fulfill the allocation request.
    """

    def __init__(self, node_type: str, node_name: str, peer_type: str, peer_name: str):
        status_code = codes.SERVICE_UNAVAILABLE
        detail = "Out of Pre-Shared Random Data (PSRD)"
        super().__init__(
            status_code,
            detail,
            node_type,
            node_name,
            peer_type=peer_type,
            peer_name=peer_name,
        )
