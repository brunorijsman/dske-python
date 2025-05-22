"""
Exceptions.
"""


class DSKEException(Exception):
    """
    Base class for all exceptions in the DSKE module.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ClientAlreadyRegisteredError(DSKEException):
    """
    Exception raised when a client is already registered.
    """

    def __init__(self, client_name: str):
        super().__init__(
            message=f"Client {client_name} is already registered.",
        )


class ClientNotRegisteredError(DSKEException):
    """
    Exception raised when a client is not registered.
    """

    def __init__(self, client_name: str):
        super().__init__(
            message=f"Client {client_name} is not registered.",
        )


class HTTPGetFailedError(DSKEException):
    """
    Exception raised when an HTTP GET request failed.
    """

    def __init__(self, url: str, params: dict, status_code: int, response: str):
        super().__init__(
            message=(
                f"HTTP GET failed. "
                f"URL: {url}. "
                f"Params: {params}. "
                f"Status code: {status_code}. "
                f"Response: {response}."
            )
        )


class HTTPPostFailedError(DSKEException):
    """
    Exception raised when an HTTP POSY request failed.
    """

    def __init__(self, url: str, json: dict, status_code: int, response: str):
        super().__init__(
            message=(
                f"HTTP GET failed. "
                f"URL: {url}. "
                f"JSON: {json}. "
                f"Status code: {status_code}. "
                f"Response: {response}."
            )
        )


class InvalidKeyIDError(DSKEException):
    """
    Exception raised when an invalid key ID is provided (not a valid UUID).
    """

    def __init__(self, key_id: str):
        super().__init__(
            message=f"Invalid key ID: {key_id}",
        )


class UnknownKeyIDError(DSKEException):
    """
    Exception raised when an unknown key ID is provided.
    """

    def __init__(self, key_id: str):
        super().__init__(
            message=f"Unknown key ID: {key_id}",
        )
