"""
The result of a client registering itself with a hub.
"""

import pydantic


class APIRegistrationRequest(pydantic.BaseModel):
    """
    Representation of a registration request as used in API calls.
    """

    client_name: str

    def __init__(self, client_name: str):
        super().__init__(client_name=client_name)


class APIRegistrationResponse(pydantic.BaseModel):
    """
    Representation of a registration response as used in API calls.
    """

    hub_name: str
