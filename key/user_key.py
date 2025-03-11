"""
A key used for encryption or for signing.
"""

import os
from uuid import UUID, uuid4

from .user_key_share import UserKeyShare


# TODO: Get rid of this class? We have to clearly distinguish between:
#       - Keys produced for the user and delivered over the ETSI QKD 014 interface (user_key)
#       - Keys consumed from PSRD and used to encrypt key-shares using one-time pads
#         (key_share_encryption_key)
#       - Keys consumed from PSRD and used to sign key-shares (key_share_signature_key)


# TODO: Perhaps move all of the common packages (psrd, key) to a single package, namely package
#       "common"?


class UserKey:
    """
    A key for the user, delivered over the ETSI QKD 014 interface.
    """

    _uuid: UUID
    _value: bytes

    def __init__(self, uuid: UUID, value: bytes):
        self._uuid = uuid
        self._value = value

    @property
    def uuid(self) -> UUID:
        """
        The UUID of the key.
        """
        return self._uuid

    @property
    def value(self) -> bytes:
        """
        The value of the key.
        """
        return self._value

    @classmethod
    def create_random_user_key(cls, size_in_bytes) -> "UserKey":
        """
        Create a random user key, with the given size in bytes.
        """
        return UserKey(uuid4(), os.urandom(size_in_bytes))

    def split_into_shares(
        self,
        nr_shares: int,
        min_nr_shares: int,
    ) -> list[UserKeyShare]:
        """
        Split a user key into `nr_shares` shares. The minimum number of shares required to
        reconstruct the user key is `min_nr_shares`.
        """
        assert nr_shares >= min_nr_shares
        # TODO: Implement Shamir's Secret Sharing algorithm
        shares = []
        for share_index in range(nr_shares):
            share = UserKeyShare(
                key_id=self._uuid,
                share_index=share_index,
                data=b"This is a share",  # TODO: Use share as produced by SSS algorithm
            )
            shares.append(share)
        return shares
