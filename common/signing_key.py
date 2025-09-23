"""
The key that is used to sign and to verify the signature on DSKE in-band protocol messages.
"""

import hashlib
import hmac
from .allocation import Allocation
from .pool import Pool
from .signature import Signature
from .utils import bytes_to_str, str_to_bytes


HEADER_NAME = "DSKE-Signing-Key"
LOWER_HEADER_NAME = HEADER_NAME.lower()

_KEY_SIZE = 32  # bytes
_ENCODING_SEPARATOR = ";"


class SigningKey:
    """
    A SigningKey is used in the application logic (as opposed to in the FastApi middleware) to sign
    and to verify the signature on DSKE in-band protocol messages.
    """

    _allocation: Allocation
    _key_data: bytes

    def __init__(self, allocation: Allocation) -> "SigningKey":
        """
        Create a SigningKey from an Allocation that was previously allocated from a Pool.
        """
        self._allocation = allocation
        self._allocation.consume()

    @classmethod
    def from_pool(cls, pool: Pool):
        """
        Allocate a new EncryptionKey from the given pool.
        """
        allocation = pool.allocate(_KEY_SIZE)
        return SigningKey(allocation)

    def to_enc_str(self) -> str:
        """
        Encode the SigningKey as a string that can be passed from the application logic to the
        middleware in a temporary header.
        The format of the string is <allocation-encoded-str>;<signature-data-str>
        """
        return (
            f"{self._allocation.to_enc_str()}"
            f"{_ENCODING_SEPARATOR}"
            f"{bytes_to_str(self._allocation.value)}"
        )

    def sign(self, signed_data_list: list[bytes | None]) -> Signature:
        """
        Sign data and return the signature.
        """
        signing_key_data = self._allocation.value
        signed_data = b""
        for signed_date_item in signed_data_list:
            if signed_date_item is not None:
                signed_data += signed_date_item
        h = hmac.new(signing_key_data, signed_data, hashlib.sha256)
        signature_data = h.digest()
        return Signature(self._allocation.to_enc_str(), signature_data)

    def add_to_headers(self, headers: dict[str, str]):
        """
        Add this SigningKey to a dictionary of HTTP headers.
        """
        headers[HEADER_NAME] = self.to_enc_str()


class MiddlewareSigningKey:
    """
    A MiddlewareSigningKey is used in the middleware (as opposed to the application logic) to sign
    and to verify the signature on DSKE in-band protocol messages. The key is allocated in the
    application logic (because that is were we have access to the pool) but the actual signing
    happens in the middleware (because that is were we have access to the fully encoded request or
    response). The key is passed from the application logic to the middleware using a temporary
    HTTP header.
    """

    def __init__(
        self, allocation_enc_str: str, key_data: bytes
    ) -> "MiddlewareSigningKey":
        """
        Should only be called from class methods from_xxx.
        """
        self._allocation_enc_str = allocation_enc_str
        self._key_data = key_data

    @classmethod
    def from_enc_str(cls, enc_str: str) -> "SigningKey":
        """
        Create an SigningKey from an encoded string as used the temporary HTTP header.
        """
        split_str = enc_str.split(_ENCODING_SEPARATOR)
        if len(split_str) != 2:
            assert False  # TODO: Raise an exception instead
        allocation_enc_str = split_str[0]
        key_data_str = split_str[1]
        key_data = str_to_bytes(key_data_str)
        return MiddlewareSigningKey(allocation_enc_str, key_data)

    @classmethod
    def extract_from_headers(cls, headers: dict[str, str]) -> "SigningKey":
        """
        Create a SigningKey from the DSKE-Signature header in a dictionary of HTTP headers.
        The header is removed from the dictionary of headers (hence the word "extract" in the
        method name)
        """
        signing_key_enc_str = headers.get(LOWER_HEADER_NAME, None)
        if signing_key_enc_str is None:
            assert False  # TODO: Raise an exception instead
        signing_key = cls.from_enc_str(signing_key_enc_str)
        del headers[LOWER_HEADER_NAME]
        return signing_key

    def sign(self, data: bytes) -> Signature:
        """
        Sign data and return the signature.
        """
        h = hmac.new(self._key_data, data, hashlib.sha256)
        signature_data = h.digest()
        return Signature(self._allocation_enc_str, signature_data)
