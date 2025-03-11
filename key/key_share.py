"""
A key share.
"""

from uuid import UUID

import key
import psrd


class KeyShare:
    """
    A key share.
    """

    def __init__(self, key_id: UUID, share_index: int, data: bin):
        self._key_id = key_id
        self._share_index = share_index
        self._data = data  # Not encrypted

    def to_protocol_json(
        self,
        encryption_key_psrd_allocation: psrd.Allocation,
        signature_key_psrd_allocation: psrd.Allocation,
    ) -> dict:
        """
        Convert to JSON representation as used in the DSKE protocol.
        """
        return {
            "key_id": str(self._key_id),
            "share_index": self._share_index,
            "encryption_key_psrd_allocation": encryption_key_psrd_allocation.to_protocol_json(),
            "encrypted_data": self._data,  # TODO: Encrypt
            "signature_key_psrd_allocation": signature_key_psrd_allocation.to_protocol_json(),
            "signature": None,  # TODO: Sign
        }

    @classmethod
    def from_protocol_json(
        cls,
        json: dict,
        _psrd_pool: psrd.Pool,
    ) -> "KeyShare":
        """
        Convert from JSON representation as used in the DSKE protocol.
        """
        _encryption_key_psrd_allocation = json[
            "encryption_key_psrd_allocation"
        ].from_protocol_json()
        _signature_key_psrd_allocation = json[
            "signature_key_psrd_allocation"
        ].from_protocol_json()
        # TODO: Consume keys from pool using allocations
        # TODO: Decrypt data
        # TODO: Verify signature
        return KeyShare(
            key_id=UUID(json["key_id"]),
            share_index=json["share_index"],
            data=json["encrypted_data"],
        )

    @classmethod
    def split_key_into_shares(
        cls,
        key_id: UUID,
        _key: bin,
        nr_shares: int,
        _min_nr_shares: int,
    ) -> list[key.KeyShare]:
        """
        Split a key into key shares.
        """
        # TODO: Implement Shamir's Secret Sharing algorithm
        shares = []
        for share_index in range(nr_shares):
            share = key.KeyShare(
                key_id=key_id,
                share_index=share_index,
                data=b"This is a share",  # TODO: Use share as produced by SSS algorithm
            )
            shares.append(share)
        return shares
