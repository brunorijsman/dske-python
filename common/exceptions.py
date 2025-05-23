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
        message = f"HTTP {method} failed."
        message += f"URL: {url}."
        if reason is not None:
            message += f" Reason: {reason}. "
        if params is not None:
            message += f" Params: {params}. "
        if data is not None:
            message += f" Data: {data}. "
        if status_code is not None:
            message += f" Status code: {status_code}. "
        if response is not None:
            message += f" Response: {response}. "
        if exception is not None:
            message += f" Exception: {exception}. "
        super().__init__(message=message)


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
