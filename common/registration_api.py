"""
Models for the registration API.
"""

import pydantic


class APIPutRegistrationRequest(pydantic.BaseModel):
    """
    Model for the PUT registration request in the API.
    """

    client_name: str

    def __init__(self, client_name: str):
        super().__init__(client_name=client_name)


class APIPutRegistrationResponse(pydantic.BaseModel):
    """
    Model for the PUT registration response in the API.
    """

    hub_name: str

    def __init__(self, hub_name: str):
        super().__init__(hub_name=hub_name)
