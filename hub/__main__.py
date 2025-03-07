"""
Main module for a DSKE security hub.
"""

from base64 import b64encode
from fastapi import FastAPI
from pydantic import PositiveInt
from .hub import Hub

APP = FastAPI()

_HUB = Hub(name="hubert", pre_shared_key_size=32)


@APP.get("/dske/oob/v1/register-dske-client")
async def get_register_dske_client(dske_client_name: str):
    """
    Out of band: Register a DSKE client.
    """
    dske_client = _HUB.register_client(dske_client_name)
    encoded_pre_shared_key = b64encode(dske_client.pre_shared_key).decode("utf-8")
    # TODO: Return a proper error when there is an exception because the client already is
    #       registered.
    return {"preSharedKey": encoded_pre_shared_key}


@APP.get("/dske/oob/v1/psrd")
async def get_psrd(size: PositiveInt):
    """
    Out of band: Get Pre-Shared Random Data (PSRD).
    """
    # TODO: Add dske_client_name. Note: we don't do authentication of out-of-band requests.
    # TODO: Add dske_client_name parameter to create_random_psrd.
    # TODO: Error if the client was not registered.
    _psrd = _HUB.create_random_psrd(size)
    return {"result": "Pre-shared random data."}


@APP.get("/dske/api/v1/status")
async def get_status():
    """
    API: Get status.
    """
    # TODO: Implement this.
    return {"result": "Status."}


@APP.post("/dske/api/v1/key-share")
async def post_key_share():
    """
    API: Post key share.
    """
    # TODO: Implement this.
    return {"result": "Post key-share result."}
