"""
Exceptions.
"""

from typing import List
from uuid import UUID
from fastapi import status


class DSKEException(Exception):
    """
    Base class for all exceptions in the DSKE module.
    """

    def __init__(self, status_code: int, message: str, details: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.details = details


class ClientNotRegisteredError(DSKEException):
    """
    Exception raised when a client is not registered.
    """

    def __init__(self, client_name: str):

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Client is not registered.",
            details={"client_name": client_name},
        )


class InvalidPoolOwnerError(DSKEException):
    """
    Exception raised when an invalid pool owner is specified.
    """

    def __init__(self, pool_owner_str: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Pool owner {pool_owner_str} is invalid.",
        )


class HTTPError(DSKEException):
    """
    Exception raised when an HTTP request failed.
    """

    def __init__(
        self,
        method: str,
        url: str,
        reason: str | None = None,
        params: dict | None = None,
        data: dict | None = None,
        status_code: int | None = None,
        response: str | None = None,
        exception: str | None = None,
    ):
        message = "HTTP request failed."
        details = {}
        details["method"] = method
        details["url"] = url
        if reason is not None:
            details["reason"] = reason
        if params is not None:
            details["params"] = params
        if data is not None:
            details["data"] = data
        if status_code is not None:
            details["status_code"] = status_code
        if response is not None:
            details["response"] = response
        if exception is not None:
            details["exception"] = exception
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            details=details,
        )


class InvalidKeyIDError(DSKEException):
    """
    Exception raised when an invalid key ID is provided (e.g. not a valid UUID).
    """

    def __init__(self, key_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid key ID.",
            details={"key_id": key_id},
        )


class KeySizeIsNotMultipleOfEightBitsError(DSKEException):
    """
    Exception raised when a key size is not a multiple of eight bits.
    """

    def __init__(self, size: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            # This exact message is required by ETSI QKD 014 (we capitalized the S though).
            message="Size shall be a multiple of 8",
            details={"size": size},
        )


class KeySizeOutOfRangeError(DSKEException):
    """
    Exception raised when a key size is out of the allowed range.
    """

    def __init__(self, size: int, min_size: int, max_size: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Key size is out of range",
            details={"size": size, "min_size": min_size, "max_size": max_size},
        )


class UnknownKeyIDError(DSKEException):
    """
    Exception raised when an unknown key ID is provided.
    """

    def __init__(self, key_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Unknown key ID",
            details={"key_ID": key_id},
        )


class CouldNotScatterEnoughSharesError(DSKEException):
    """
    Unable to scatter enough shares to peer hubs.
    """

    def __init__(
        self,
        key_id: UUID,
        nr_successful_shares: int,
        nr_required_shares: int,
        causes=List[str],
    ):
        details = {
            "key_id": str(key_id),
            "nr_successful_shares": nr_successful_shares,
            "nr_required_shares": nr_required_shares,
        }
        if causes:
            details["causes"] = causes
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Could not scatter enough shares for key.",
            details=details,
        )


class CouldNotGatherEnoughSharesError(DSKEException):
    """
    Unable to gather enough shares from peer hubs.
    """

    def __init__(
        self,
        key_id: UUID,
        nr_successful_shares: int,
        nr_required_shares: int,
        causes=List[str],
    ):
        details = {
            "key_id": str(key_id),
            "nr_successful_shares": nr_successful_shares,
            "nr_required_shares": nr_required_shares,
        }
        if causes:
            details["causes"] = causes
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Could not gather enough shares for key.",
            details=details,
        )


class ShamirSplitError(DSKEException):
    """
    Exception raised when splitting a secret using Shamir's Secret Sharing fails.
    """

    def __init__(self, key_id: UUID, reason: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to split secret using Shamir's Secret Sharing.",
            details={"key_id": str(key_id), "reason": reason},
        )


class ShamirReconstructError(DSKEException):
    """
    Exception raised when reconstructing a secret using Shamir's Secret Sharing fails.
    """

    def __init__(self, key_id: UUID, reason: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to reconstruct secret using Shamir's Secret Sharing.",
            details={"key_id": str(key_id), "reason": reason},
        )


class OutOfPreSharedRandomDataError(DSKEException):
    """
    Out of Pre-Shared Random Data (PSRD). We tried to allocated some pre-shared random data from
    a pool, but the pool did not contain enough free data to fulfill the allocation request.
    """

    def __init__(
        self,
        pool_descr: str,
        purpose: str,
        allocation_size,
        pool_available_bytes: int,
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=f"Pool {pool_descr} out of Pre-Shared Random Data (PSRD).",
            details={
                "purpose": purpose,
                "allocation_size": allocation_size,
                "pool_available_bytes": pool_available_bytes,
            },
        )
