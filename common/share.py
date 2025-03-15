"""
A share of a key.
"""

from uuid import UUID
import pydantic
from .allocation import Allocation, APIAllocation
from .common import bytes_to_str, str_to_bytes, to_mgmt
from .pool import Pool


class APIShare(pydantic.BaseModel):
    """
    Representation of a key share as used in API calls.
    """

    # TODO: Provide a better example in the generated documentation page
    # TODO: Add a seq_nr field to the API for replay attack prevention

    client_name: str
    key_id: str
    share_index: int
    encrypted_value: str  # Base64 encoded
    encryption_key_allocation: APIAllocation
    signature_key_allocation: APIAllocation


class Share:
    """
    A share of a key. A key is split up into multiple (`nr_shares`) key shares. The user
    key can be reconstructed from a subset (`min_nr_shares`) of these key shares.
    """

    _AUTHENTICATION_KEY_SIZE_IN_BYTES = 2

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        key_uuid: UUID,
        share_index: int,
        value: bytes,
        encryption_key_allocation: Allocation | None = None,
        signature_key_allocation: Allocation | None = None,
    ):
        self._key_uuid = key_uuid
        self._share_index = share_index
        self._value = value  # Not encrypted
        self._encrypted_value = None
        self._encryption_key_allocation = encryption_key_allocation
        self._signature_key_allocation = signature_key_allocation

    @property
    def key_uuid(self) -> UUID:
        """
        Get the key UUID.
        """
        return self._key_uuid

    @property
    def share_index(self) -> int:
        """
        Get the share index.
        """
        return self._share_index

    @property
    def value(self) -> bytes:
        """
        Get the (unencrypted) value.
        """
        return self._value

    @property
    def encryption_key_allocation(self) -> bytes:
        """
        Get the encryption key PSRD allocation.
        """
        return self._encryption_key_allocation

    @property
    def signature_key_allocation(self) -> bytes:
        """
        Get the signature key PSRD allocation.
        """
        return self._signature_key_allocation

    def __repr__(self) -> str:
        """
        Get a string representation.
        """
        return str(self.to_mgmt())

    def to_mgmt(self):
        """
        Get the management status.
        """
        return {
            "key_uuid": str(self._key_uuid),
            "share_index": self._share_index,
            "value": bytes_to_str(self._value, truncate=True),
            "encrypted_value": bytes_to_str(self._encrypted_value, truncate=True),
            "encryption_key_allocation": to_mgmt(self._encryption_key_allocation),
            "signature_key_allocation": to_mgmt(self._signature_key_allocation),
        }

    def allocate_encryption_and_authentication_keys_from_pool(self, pool: Pool):
        """
        Allocate encryption and authentication keys from the pool.
        """
        # TODO: Error handling: if either fails, return the other the pool and raise an exception
        # We use one-time pad encryption for the share, so the encryption key must have the same
        # length as the data in the share.
        encryption_key_size_in_bytes = len(self._value)
        self._encryption_key_allocation = pool.allocate(encryption_key_size_in_bytes)
        self._signature_key_allocation = pool.allocate(
            self._AUTHENTICATION_KEY_SIZE_IN_BYTES
        )

    def encrypt(self):
        """
        Encrypt the value, using encryption_key_allocation as a one-time pad encryption key.
        """
        assert self._value is not None
        assert self._encryption_key_allocation is not None
        encryption_key = self._encryption_key_allocation.consume()
        assert encryption_key is not None
        assert len(self._value) == len(encryption_key)
        encrypted_byte_list = [
            value_byte ^ encryption_key_byte
            for value_byte, encryption_key_byte in zip(self._value, encryption_key)
        ]
        self._encrypted_value = bytes(encrypted_byte_list)

    def sign(self):
        """
        Create a signature over selected fields in the key share, using
        signature_key_allocation signing secret.
        """
        assert self._value is not None
        assert self._signature_key_allocation is not None
        _signature_key = self._signature_key_allocation.consume()
        # TODO: Finish this

    @classmethod
    def from_api(cls, api_share: APIShare, pool: Pool) -> "Share":
        """
        Create a Share from an APIShare.
        """
        return Share(
            key_uuid=UUID(api_share.key_id),
            share_index=api_share.share_index,
            value=str_to_bytes(api_share.encrypted_value),
            encryption_key_allocation=Allocation.from_api(
                api_share.encryption_key_allocation, pool
            ),
            signature_key_allocation=Allocation.from_api(
                api_share.signature_key_allocation, pool
            ),
        )

    def to_api(self, client_name) -> APIShare:
        """
        Create an APIShare from a Share.
        """
        api_share = APIShare(
            client_name=client_name,
            key_id=str(self._key_uuid),
            share_index=self._share_index,
            encrypted_value=bytes_to_str(self._value),
            encryption_key_allocation=self._encryption_key_allocation.to_api(),
            signature_key_allocation=self._signature_key_allocation.to_api(),
        )
        return api_share
