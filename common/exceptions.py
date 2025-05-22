"""
Exceptions.
"""

from fastapi import HTTPException


class ClientAlreadyRegisteredError(HTTPException):
    """
    Exception raised when a client is already registered.
    """

    def __init__(self, client_name: str):
        super().__init__(
            status_code=400,
            detail=f"Client {client_name} is already registered.",
        )


class ClientNotRegisteredError(HTTPException):
    """
    Exception raised when a client is not registered.
    """

    def __init__(self, client_name: str):
        super().__init__(
            status_code=400,
            detail=f"Client {client_name} is not registered.",
        )


class InvalidKeyIDError(HTTPException):
    """
    Exception raised when an invalid key ID is provided.
    """

    def __init__(self, key_id: str):
        super().__init__(
            status_code=400,
            detail=f"Invalid key ID: {key_id}",
        )


class UnknownKeyIDError(HTTPException):
    """
    Exception raised when an unknown key ID is provided.
    """

    def __init__(self, key_id: str):
        super().__init__(
            status_code=400,
            detail=f"Unknown key ID: {key_id}",
        )
