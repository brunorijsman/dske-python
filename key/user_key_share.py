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

    def __init__(self, user_key_uuid: UUID, share_index: int, value: bytes):
        self._user_key_uuid = user_key_uuid
        self._share_index = share_index
        self._value = value  # Not encrypted

    def to_management_json(self):
        """
        Get the management status.
        """
        return {
            "user_key_uuid": str(self._user_key_uuid),
            "share_index": self._share_index,
            "value": common.bytes_to_str(self._value, truncate=True),
        }

    def __repr__(self) -> str:
        """
        Get a string representation.
        """
        return str(self.to_management_json())

    def to_protocol_json(self) -> dict:
        """
        Convert to JSON representation as used in the DSKE protocol.
        """
        return {
            "user_key_uuid": str(self._user_key_uuid),
            "share_index": self._share_index,
            "value": common.bytes_to_str(self._value, truncate=True),
        }

    @classmethod
    def from_protocol_json(
        cls,
        json: dict,
        _psrd_pool: psrd.Pool,
    ) -> "UserKeyShare":
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
        return UserKeyShare(
            user_key_uuid=UUID(json["key_id"]),
            share_index=json["share_index"],
            value=json["encrypted_data"],
        )
