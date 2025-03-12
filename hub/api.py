"""
The public API exposed by the hub.
"""

# TODO: Elaborate in the doc string.
# TODO: Move the actual API endpoints @APP here, if possible

import uuid

import pydantic

import common
import key


class APIKeyShare(pydantic.BaseModel):
    """
    Key share data model, used in the following hub API endpoints:
    - POST /dske/hub/api/v1/key-share
    """

    # TODO: Provide a better example in the generated documentation page

    key_id: str
    share_index: int
    encrypted_value: str  # Base64 encoded
    # TODO: Add encryption key and signature key allocations

    def to_user_key_share(self) -> key.UserKeyShare:
        """
        Create a UserKeyShare from an APIKeyShare.
        """
        return key.UserKeyShare(
            user_key_uuid=uuid.UUID(self.key_id),
            share_index=self.share_index,
            value=common.str_to_bytes(self.encrypted_value),  # TODO: decrypt
        )

    @classmethod
    def from_user_key_share(cls, user_key_share: key.UserKeyShare) -> "APIKeyShare":
        """
        Create an APIKeyShare from a UserKeyShare.
        """
        return APIKeyShare(
            key_id=str(user_key_share.user_key_uuid),
            share_index=user_key_share.share_index,
            encrypted_value=common.bytes_to_str(user_key_share.value),  # TODO: encrypt
        )
