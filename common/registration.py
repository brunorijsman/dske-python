"""
The result of a client registering itself with a hub.
"""

import pydantic


class APIRegistration(pydantic.BaseModel):
    """
    Representation of a registration result as used in API calls.
    """

    hub_name: str
    pre_shared_key: str
