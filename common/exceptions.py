"""
Exceptions.
"""

import json
from typing import List
from uuid import UUID
from fastapi import status
from .logging import LOGGER


class DSKEException(Exception):
    """
    Base class for all exceptions in the DSKE module.
    """

    def __init__(self, status_code: int, message: str, details: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.details = details
        try:
            log_message = f"DSKEException raised: {message}"
            if details is not None:
                log_message += f" Details: {json.dumps(details)}"
            LOGGER.error(log_message)
        except Exception:  # pylint: disable=broad-except
            pass


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


class InvalidOwnerError(DSKEException):
    """
    Exception raised when an invalid pool owner is specified.
    """

    def __init__(self, owner_str: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Owner {owner_str} is invalid.",
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
        if status_code is None:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        details = {}
        details["method"] = method
        details["url"] = url
        if reason is not None:
            details["reason"] = reason
        if params is not None:
            details["params"] = params
        if data is not None:
            details["data"] = data
        details["status_code"] = status_code
        if response is not None:
            details["response"] = response
        if exception is not None:
            details["exception"] = exception
        explain = ""
        if response is not None:
            try:
                response_json = json.loads(response)  # type: ignore
                if "message" in response_json:
                    explain = f" - {response_json['message']}"
            except Exception:  # pylint: disable=broad-except
                pass
        message = f"HTTP request failed ({method} {url}: {status_code}{explain})."
        super().__init__(status_code=status_code, message=message, details=details)


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

    def __init__(self, key_id: UUID):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Unknown key ID",
            details={"key_ID": str(key_id)},
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
        status_code: int,
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
            status_code=status_code,
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
        status_code: int,
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
            status_code=status_code,
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


class InvalidSignatureError(DSKEException):
    """
    Exception raised when a signature is invalid.
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Invalid signature.",
        )


class InvalidBlockUUIDError(DSKEException):
    """
    Exception raised when a PSRD block UUID is invalid.
    """

    def __init__(self, block_uuid: str | UUID):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid PSRD block UUID.",
            details={"block_uuid": str(block_uuid)},
        )


class InvalidPSRDIndex(DSKEException):
    """
    Exception raised when the byte index into PSRD data is invalid.
    """

    def __init__(self, block_uuid: UUID, index: str | int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid byte index into PSRD block.",
            details={"block_uuid": str(block_uuid), "index": index},
        )


class PSRDDataAlreadyUsedError(DSKEException):
    """
    Exception raised when an attempt is made to use PSRD data more than once.
    """

    def __init__(self, block_uuid: UUID, start: int, size: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Attempt to use PSRD data more than once.",
            details={
                "block_uuid": str(block_uuid),
                "start": start,
                "size": size,
            },
        )


class InvalidPSRDDataError(DSKEException):
    """
    Exception raised when the PSRD data received from a hub is invalid.
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="PSRD data is invalid.",
        )


class InvalidEncodedFragmentError(DSKEException):
    """
    Exception raised when trying to parse an encoded fragment string that is invalid.
    """

    def __init__(self, encoded_fragment: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid encoded fragment.",
            details={"encoded_fragment": encoded_fragment},
        )


class InvalidEncodedSignatureError(DSKEException):
    """
    Exception raised when trying to parse an encoded signature string that is invalid.
    """

    def __init__(self, encoded_signature: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid encoded signature.",
            details={"encoded_signature": encoded_signature},
        )


class InvalidEncodedSigningKeyError(DSKEException):
    """
    Exception raised when trying to parse an encoded signing key string that is invalid.
    """

    def __init__(self, encoded_signing_key: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid encoded signing key.",
            details={"encoded_signing_key": encoded_signing_key},
        )


class EncryptorNotConnectedToClientError(DSKEException):
    """
    Exception raised when an encryptor is not registered for a client.
    """

    def __init__(self, client_name: str, encryptor_name: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Encryptor is not connected to client.",
            details={
                "client_name": client_name,
                "encryptor_name": encryptor_name,
            },
        )


class MissingAuthorizationHeaderError(DSKEException):
    """
    Exception raised when the Authorization header is missing.
    """

    def __init__(self, client_name: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Missing Authorization header",
            details={
                "client_name": client_name,
            },
        )


class WrongMasterSAEIDError(DSKEException):
    """
    Exception raised when the master SAE ID in a Get key with key IDs request does not match
    the master SAE ID used in the original Get key request.
    """

    def __init__(self, requested_master_sae_id: str, share_master_sae_id, key_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Master SAE ID does not match the one used in the original Get key request.",
            details={
                "requested_master_sae_id": requested_master_sae_id,
                "share_master_sae_id": share_master_sae_id,
                "key_id": key_id,
            },
        )


class WrongSlaveSAEIDError(DSKEException):
    """
    Exception raised when the slave SAE ID in a Get key with key IDs request does not match
    the slave SAE ID used in the original Get key request.
    """

    def __init__(self, requested_master_sae_id: str, share_master_sae_id, key_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Slave SAE ID does not match the one used in the original Get key request.",
            details={
                "requested_master_sae_id": requested_master_sae_id,
                "share_master_sae_id": share_master_sae_id,
                "key_id": key_id,
            },
        )
