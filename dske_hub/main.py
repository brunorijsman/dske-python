"""
Main module for the DSKE security hub.
"""

from base64 import b64encode
from dske_hub import DSKEHub
from fastapi import FastAPI
from pydantic import PositiveInt

APP = FastAPI()

DSKE_HUB = DSKEHub(name="hubert", pre_shared_key_size=32)


@APP.get("/dske/oob/v1/register-dske-client")
async def get_register_dske_client(dske_client_name: str):
    """
    Out of band: Register DSKE client.
    """
    dske_client = DSKE_HUB.register_dske_client(dske_client_name)
    encoded_pre_shared_key = b64encode(dske_client.pre_shared_key).decode('utf-8')
    return {"preSharedKey": encoded_pre_shared_key}


@APP.get("/dske/oob/v1/psrd")
async def get_psrd(size: PositiveInt):
    """
    Out of band: Get Pre-Shared Random Data (PSRD).
    """
    # TODO: Implement this.
    _psrd = DSKE_HUB.create_random_psrd(size)
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
