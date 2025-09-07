"""
A share of a key.
"""

from uuid import UUID
from .allocation import Allocation
from .utils import bytes_to_str, to_mgmt
from .pool import Pool


class Share:
    """
    A share of a user key. A user key is split up into multiple (`nr_shares`) `shares. The user key
    can be reconstructed from a subset (`min_nr_shares`) of these shares.
    """

    def __init__(
        self,
        user_key_uuid: UUID,
        share_index: int,
        value: bytes | None = None,
        encrypted_value: bytes | None = None,
        encryption_key_allocation: Allocation | None = None,
    ):
        self._user_key_uuid = user_key_uuid
        self._share_index = share_index
        self._value = value
        self._encrypted_value = encrypted_value
        self._encryption_key_allocation = encryption_key_allocation

    @property
    def user_key_uuid(self) -> UUID:
        """
        Get the user key UUID.
        """
        return self._user_key_uuid

    @property
    def share_index(self) -> int:
        """
        Get the share index.
        """
        return self._share_index

    @property
    def value(self) -> bytes:
        """
        Get the (unencrypted) share value.
        """
        return self._value

    @property
    def encryption_key_allocation(self) -> bytes:
        """
        Get the encryption key PSRD allocation.
        """
        return self._encryption_key_allocation

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
            "key_uuid": str(self._user_key_uuid),
            "share_index": self._share_index,
            "value": bytes_to_str(self._value, truncate=True),
            "encrypted_value": bytes_to_str(self._encrypted_value, truncate=True),
            "encryption_key_allocation": to_mgmt(self._encryption_key_allocation),
        }

    def allocate_encryption_key_from_pool(self, pool: Pool):
        """
        Allocate encryption key from the pool.
        """
        # We use one-time pad encryption for the share, so the encryption key must have the same
        # length as the data in the share.
        encryption_key_size_in_bytes = len(self._value)
        self._encryption_key_allocation = pool.allocate(encryption_key_size_in_bytes)

    def encrypt(self):
        """
        Encrypt the value, using encryption_key_allocation as a one-time pad encryption key.
        """
        assert self._value is not None
        assert self._encrypted_value is None
        assert self._encryption_key_allocation is not None
        encryption_key = self._encryption_key_allocation.consume()
        assert encryption_key is not None
        assert len(self._value) == len(encryption_key)
        encrypted_byte_list = [
            value_byte ^ encryption_key_byte
            for value_byte, encryption_key_byte in zip(self._value, encryption_key)
        ]
        self._encrypted_value = bytes(encrypted_byte_list)

    def decrypt(self):
        """
        Decrypt the value, using encryption_key_allocation as a one-time pad encryption key.
        """
        assert self._encrypted_value is not None
        assert self._value is None
        assert self._encryption_key_allocation is not None
        encryption_key = self._encryption_key_allocation.consume()
        assert encryption_key is not None
        assert len(self._encrypted_value) == len(encryption_key)
        decrypted_byte_list = [
            value_byte ^ encryption_key_byte
            for value_byte, encryption_key_byte in zip(
                self._encrypted_value, encryption_key
            )
        ]
        self._value = bytes(decrypted_byte_list)
        self._encrypted_value = None
        self._encryption_key_allocation = None
