"""
The signature for a DSKE in-band protocol message.
"""

from typing import Optional
from .utils import bytes_to_str, str_to_bytes

HEADER_NAME = "DSKE-Signature"
LOWER_HEADER_NAME = HEADER_NAME.lower()
_ENCODING_SEPARATOR = "%"


class Signature:
    """
    The signature for a DSKE in-band protocol message.
    """

    _signing_key_allocation_enc_str: str
    _signature_data: bytes

    def __init__(self, signing_key_allocation_enc_str: str, signature_data: bytes):
        self._signing_key_allocation_enc_str = signing_key_allocation_enc_str
        self._signature_data = signature_data

    @property
    def signing_key_allocation_enc_str(self) -> str:
        """
        Get the signing key allocation encoded string.
        """
        return self._signing_key_allocation_enc_str

    def same_as(self, other: "Signature") -> bool:
        """
        Check if this signature is the same as another signature.
        """
        # pylint: disable=protected-access
        if (
            self._signing_key_allocation_enc_str
            != other._signing_key_allocation_enc_str
        ):
            return False
        if self._signature_data != other._signature_data:
            return False
        return True

    @classmethod
    def from_enc_str(cls, enc_str: str) -> "Signature":
        """
        Create a Signature from an encoded string as used in an HTTP header or URL parameter.
        The format of the string is <allocation-encoded-str>%<signature-data-str>
        """
        split_str = enc_str.split(_ENCODING_SEPARATOR)
        if len(split_str) != 2:
            assert False  # TODO: Raise an exception instead
        allocation_enc_str = split_str[0]
        signature_data_str = split_str[1]
        signature_data = str_to_bytes(signature_data_str)
        return Signature(allocation_enc_str, signature_data)

    def to_enc_str(self) -> str:
        """
        Encode a Signature as a string that can be used in HTTP headers or URL parameters.
        The format of the string is <allocation-encoded-str>%<signature-data-str>
        """
        return (
            f"{self._signing_key_allocation_enc_str}"
            f"{_ENCODING_SEPARATOR}"
            f"{bytes_to_str(self._signature_data)}"
        )

    def add_to_headers(self, headers: dict[str, str]):
        """
        Add this signature to a dictionary of HTTP headers.
        """
        headers[HEADER_NAME] = self.to_enc_str()

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> Optional["Signature"]:
        """
        Create a Signature from the DSKE-Signature header in a dictionary of HTTP headers. Returns
        None if the header is not present.
        """
        signature_enc_str = headers.get(LOWER_HEADER_NAME, None)
        if signature_enc_str is None:
            return None
        signature = cls.from_enc_str(signature_enc_str)
        return signature
