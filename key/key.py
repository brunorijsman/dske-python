"""
A key used for encryption or for signing.
"""

from uuid import UUID

from . import KeyShare


class Key:
    """
    A key used for encryption or for signing.
    """

    def __init__(self, key_id: UUID):
        self._key_id = key_id

    def split_into_shares(self, nr_shares: int, _min_nr_shares: int) -> list[KeyShare]:
        """
        Split a key into key `nr_shares` key shares. The minimum number of shares required to
        reconstruct the key is `min_nr_shares`.
        """
        # TODO: Implement Shamir's Secret Sharing algorithm
        shares = []
        for share_index in range(nr_shares):
            share = KeyShare(
                key_id=self._key_id,
                share_index=share_index,
                data=b"This is a share",  # TODO: Use share as produced by SSS algorithm
            )
            shares.append(share)
        return shares
