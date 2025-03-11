"""
A key used for encryption or for signing.
"""

import os
from uuid import UUID, uuid4

from .user_key_share import UserKeyShare
from .shamir import split_binary_secret_into_shares


class UserKey:
    """
    A key for the user, delivered over the ETSI QKD 014 interface.
    """

    _user_key_uuid: UUID
    _value: bytes

    def __init__(self, user_key_uuid: UUID, value: bytes):
        self._user_key_uuid = user_key_uuid
        self._value = value

    @property
    def user_key_uuid(self) -> UUID:
        """
        The UUID of the user key.
        """
        return self._user_key_uuid

    @property
    def value(self) -> bytes:
        """
        The value of the user key.
        """
        return self._value

    @classmethod
    def create_random_user_key(cls, size_in_bytes) -> "UserKey":
        """
        Create a random user key, with the given size in bytes.
        """
        return UserKey(uuid4(), os.urandom(size_in_bytes))

    def split_into_user_key_shares(
        self,
        nr_shares: int,
        min_nr_shares: int,
    ) -> list[UserKeyShare]:
        """
        Split a user key into `nr_shares` shares. The minimum number of shares required to
        reconstruct the user key is `min_nr_shares`.

        The shares do *not* yet have an encryption key or a signature key allocated. This is done
        later when each share is associated with a peer node.
        """
        binary_shares = split_binary_secret_into_shares(
            self._value, nr_shares, min_nr_shares
        )
        user_key_shares = []
        for share_index, share_value in binary_shares:
            # TODO: Error handling?
            user_key_share = UserKeyShare(self._user_key_uuid, share_index, share_value)
            user_key_shares.append(user_key_share)
        return user_key_shares
