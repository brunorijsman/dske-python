"""
A share of a user key.
"""

from uuid import UUID

import common
import psrd


class UserKeyShare:
    """
    A share of a user key. A user key is split up into multiple (`nr_shares`) key shares. The user
    key can be reconstructed from a subset (`min_nr_shares`) of these key shares.
    """

    _AUTHENTICATION_KEY_SIZE_IN_BYTES = 2

    def __init__(self, user_key_uuid: UUID, share_index: int, value: bytes):
        self._user_key_uuid = user_key_uuid
        self._share_index = share_index
        self._value = value  # Not encrypted
        self._encryption_key_psrd_allocation = None
        self._signature_key_psrd_allocation = None

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
        Get the (unencrypted) value.
        """
        return self._value

    def __repr__(self) -> str:
        """
        Get a string representation.
        """
        return str(self.to_mgmt_dict())

    def to_mgmt_dict(self):
        """
        Get the management status.
        """
        return {
            "user_key_uuid": str(self._user_key_uuid),
            "share_index": self._share_index,
            "value": common.bytes_to_str(self._value, truncate=True),
            "encryption_key_psrd_allocation": common.to_mgmt_dict(
                self._encryption_key_psrd_allocation
            ),
            "signature_key_psrd_allocation": common.to_mgmt_dict(
                self._signature_key_psrd_allocation
            ),
        }

    def allocate_encryption_and_authentication_psrd_keys_from_pool(
        self, psrd_pool: psrd.Pool
    ):
        """
        Allocate encryption and authentication PSRD keys from the pool.
        """
        # TODO: Error handling: if either fails, return the other the pool and raise an exception
        # We use one-time pad encryption for the share, so the encryption key must have the same
        # length as the data in the share.
        encryption_key_size_in_bytes = len(self._value)
        self._encryption_key_psrd_allocation = psrd_pool.allocate_allocation(
            encryption_key_size_in_bytes
        )
        self._signature_key_psrd_allocation = psrd_pool.allocate_allocation(
            self._AUTHENTICATION_KEY_SIZE_IN_BYTES
        )

    def consume_encryption_and_authentication_psrd_keys(self):
        """
        Consume the encryption and authentication PSRD keys. This cannot fail since they were
        allocated successfully allocated.
        """
        assert self._encryption_key_psrd_allocation is not None
        self._encryption_key_psrd_allocation.consume()
        assert self._signature_key_psrd_allocation is not None
        self._signature_key_psrd_allocation.consume()
