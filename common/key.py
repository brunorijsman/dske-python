"""
A key used for encryption or for signing.
"""

import os
from uuid import UUID, uuid4
from .shamir import (
    split_binary_secret_into_shares,
    # reconstruct_binary_secret_from_shares,
)
from .share import Share


class Key:
    """
    A key for the user, delivered over the ETSI QKD 014 interface.
    """

    _key_uuid: UUID
    _value: bytes

    def __init__(self, key_uuid: UUID, value: bytes):
        self._key_uuid = key_uuid
        self._value = value

    @property
    def key_uuid(self) -> UUID:
        """
        The UUID of the key.
        """
        return self._key_uuid

    @property
    def value(self) -> bytes:
        """
        The value of the key.
        """
        return self._value

    @classmethod
    def create_random_key(cls, size_in_bytes) -> "Key":
        """
        Create a random key, with the given size in bytes.
        """
        return Key(uuid4(), os.urandom(size_in_bytes))

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
            share = Share(self._key_uuid, share_index, value=share_value)
            shares.append(share)
        return shares

    # TODO: This is currently not used; should it?
    # @classmethod
    # def reconstruct_from_shares(
    #     cls,
    #     key_uuid: UUID,
    #     shares: list[Share],
    # ) -> "Key":
    #     """
    #     Reconstruct a key from a list of key shares.
    #     """
    #     share_indexes_and_values = [
    #         (share.share_index, share.value) for share in shares
    #     ]
    #     binary_secret = reconstruct_binary_secret_from_shares(share_indexes_and_values)
    #     key = Key(key_uuid, binary_secret)
    #     return key
