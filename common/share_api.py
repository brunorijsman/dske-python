"""
Models for the share key API.
"""

import pydantic
from .allocation import APIAllocation


class APIPostShareRequest(pydantic.BaseModel):
    """
    Model for the POST share request in the API.
    """

    client_name: str
    user_key_uuid: str
    share_index: int
    encrypted_value: str  # Base64 encoded
    encryption_key_allocation: APIAllocation

    def __init__(
        self,
        client_name: str,
        user_key_uuid: str,
        share_index: int,
        encrypted_value: str,
        encryption_key_allocation: APIAllocation,
    ):
        super().__init__(
            client_name=client_name,
            user_key_uuid=user_key_uuid,
            share_index=share_index,
            encrypted_value=encrypted_value,
            encryption_key_allocation=encryption_key_allocation,
        )


class APIGetShareRequest(pydantic.BaseModel):
    """
    Model for the GET share request in the API.
    """

    client_name: str
    user_key_uuid: str
    share_index: int
    encryption_key_allocation: APIAllocation

    def __init__(
        self,
        client_name: str,
        user_key_uuid: str,
        share_index: int,
        encryption_key_allocation: APIAllocation,
    ):
        super().__init__(
            client_name=client_name,
            user_key_uuid=user_key_uuid,
            share_index=share_index,
            encryption_key_allocation=encryption_key_allocation,
        )


class APIGetShareResponse(pydantic.BaseModel):
    """
    Model for the GET share response in the API.
    """

    encrypted_value: str  # Base64 encoded

    def __init__(self, encrypted_value: str):
        super().__init__(encrypted_value=encrypted_value)
