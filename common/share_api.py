"""
Models for the share key API.
"""

import pydantic
from common.allocation import APIAllocation


class APIPostShareRequest(pydantic.BaseModel):
    """
    Model for the POST share request in the API.
    """

    client_name: str
    user_key_id: str
    share_index: int
    encryption_key_allocation: APIAllocation
    encrypted_share_value: str  # Base64 encoded

    def __init__(
        self,
        client_name: str,
        user_key_id: str,
        share_index: int,
        encryption_key_allocation: APIAllocation,
        encrypted_share_value: str,  # Base64 encoded
    ):
        super().__init__(
            client_name=client_name,
            user_key_id=user_key_id,
            share_index=share_index,
            encryption_key_allocation=encryption_key_allocation,
            encrypted_share_value=encrypted_share_value,
        )


class APIGetShareResponse(pydantic.BaseModel):
    """
    Model for the GET share response in the API.
    """

    share_index: int
    encryption_key_allocation: APIAllocation
    encrypted_share_value: str  # Base64 encoded

    def __init__(
        self,
        share_index: int,
        encryption_key_allocation: APIAllocation,
        encrypted_share_value: str,
    ):
        super().__init__(
            share_index=share_index,
            encryption_key_allocation=encryption_key_allocation,
            encrypted_share_value=encrypted_share_value,
        )
