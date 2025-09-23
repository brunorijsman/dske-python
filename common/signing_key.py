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
        Should only be called from class methods from_xxx.
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
        return Signature(self._allocation, signature_data)

    def add_to_headers(self, headers: dict[str, str]):
        """
        Add this SigningKey to a dictionary of HTTP headers.
        """
        headers[HEADER_NAME] = self.to_enc_str()

    # TODO: Remove this $$$
    # def make_authentication_header(
    #     self,
    #     params: bytes | None,
    #     content: bytes | None,
    # ) -> str:
    #     """
    #     Create the value for the DSKE-Signature header for a request with the given query
    #     parameters and content.
    #     TODO: Add a nonce to prevent replay attacks.
    #     TODO: Should we also sign the URL path?
    #     """
    #     assert params is not None or content is not None
    #     signed_data = b""
    #     if params is not None:
    #         signed_data += params
    #     if content is not None:
    #         signed_data += content
    #     allocation_str = self._allocation.to_enc_str()
    #     signing_key_bin = self._allocation.value
    #     header_value = self.make_authentication_header_from_allocation_str(
    #         allocation_str, signing_key_bin, signed_data
    #     )
    #     return header_value

    # TODO: Remove this $$$
    # TODO: Not a static method but stand-alone method. Ditto for next.
    # @staticmethod
    # def make_authentication_header_from_allocation_str(
    #     allocation_str: str, signing_key_bin: bytes, signed_data: bytes
    # ) -> str:
    #     """
    #     Create the value for the DSKE-Signature header from the given allocation string and
    #     signing key.
    #     """
    #     h = hmac.new(signing_key_bin, signed_data, hashlib.sha256)
    #     signature_bin = h.digest()
    #     signature_str = bytes_to_str(signature_bin)
    #     header_value = f"{allocation_str};{signature_str}"
    #     return header_value

    # TODO: Remove this $$$
    # @staticmethod
    # def check_authentication_header(
    #     pool: Pool,
    #     params: bytes | None,
    #     content: bytes | None,
    #     authentication_header: str,
    # ) -> bool:
    #     """
    #     Check the authentication header for a request with the given query parameters and content.
    #     """
    #     split_str = authentication_header.split(";")
    #     if len(split_str) != 2:
    #         print("Authentication mismatch", file=sys.stderr)  # TODO $$$
    #         return False
    #     allocation_str = split_str[0]
    #     signature_str = split_str[1]
    #     allocation = Allocation.from_param_str(allocation_str, pool)
    #     signing_key = InternalKey.from_allocation(allocation)
    #     signature_bin = str_to_bytes(signature_str)
    #     assert params is not None or content is not None
    #     signed_data = b""
    #     if params is not None:
    #         signed_data += params
    #     if content is not None:
    #         signed_data += content
    #     if signing_key.sign(signed_data) == signature_bin:
    #         print("Authentication succeeded", file=sys.stderr)  # TODO $$$
    #         return True
    #     allocation.deallocate()
    #     print("Authentication mismatch", file=sys.stderr)  # TODO $$$
    #     return False


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
