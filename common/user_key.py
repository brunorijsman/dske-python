"""
A key that produced by the DSKE protocol, intended to be delivered to the user over a key delivery
interface such as ETSI QKD 014.

This key (intended to be delivery to the user) must not be confused with the keys that are used
internally within the DSKE protocol to encrypt key shares and to authenticate DSKE protocol
messages (see class InternalKeys).
"""

import os
from uuid import UUID, uuid4
from .shamir import (
    split_binary_secret_into_shares,
    # reconstruct_binary_secret_from_shares,
)
from .share import Share


class UserKey:
    """
    A key for the user, delivered over the ETSI QKD 014 interface.
    """

    _key_id: UUID
    _value: bytes

    def __init__(self, key_id: UUID, value: bytes):
        self._key_id = key_id
        self._value = value

    @property
    def key_id(self) -> UUID:
        """
        The UUID of the key.
        """
        return self._key_id

    @property
    def value(self) -> bytes:
        """
        The value of the key.
        """
        return self._value

    @property
    def size(self) -> int:
        """
        The size of the key in bytes.
        """
        return len(self._value)

    @classmethod
    def create_random_key(cls, size_in_bytes) -> "UserKey":
        """
        Create a random key, with the given size in bytes.
        """
        return UserKey(uuid4(), os.urandom(size_in_bytes))

    def split_into_shares(
        self,
        nr_shares: int,
        min_nr_shares: int,
    ) -> list[Share]:
        """
        Split a key into `nr_shares` shares. The minimum number of shares required to
        reconstruct the key is `min_nr_shares`.

        The shares do *not* yet have an encryption key or a signature key allocated. This is done
        later when each share is associated with a peer node.
        """
        share_indexes_and_values = split_binary_secret_into_shares(
            self._value, nr_shares, min_nr_shares
        )
        shares = []
        for share_index, share_value in share_indexes_and_values:
            # TODO: Error handling?
            share = Share(self._key_id, share_index, value=share_value)
            shares.append(share)
        return shares

    # TODO: This is currently not used; should it?
    # @classmethod
    # def reconstruct_from_shares(
    #     cls,
    #     key_id: UUID,
    #     shares: list[Share],
    # ) -> "Key":
    #     """
    #     Reconstruct a key from a list of key shares.
    #     """
    #     share_indexes_and_values = [
    #         (share.share_index, share.value) for share in shares
    #     ]
    #     binary_secret = reconstruct_binary_secret_from_shares(share_indexes_and_values)
    #     key = Key(key_id, binary_secret)
    #     return key
