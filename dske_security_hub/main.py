"""
Main module for the DSKE security hub.
"""

from fastapi import FastAPI

app = FastAPI()


@app.get("dske/oob/v1/pre-shared-keys")
async def get_pre_shared_keys():
    """
    Out of band: Get pre-shared keys.
    """
    # TODO: Implement this.
    return {"result": "Pre-shared keys"}


@app.get("dske/oob/v1/pre-shared-random-data")
async def get_pre_shared_random_data():
    """
    Out of band: Get a block of Pre-Shared Random Data (PSRD).
    """
    # TODO: Implement this.
    return {"result": "Pre-shared random data."}


@app.get("dske/api/v1/status")
async def get_status():
    """
    API: Get status
    """
    # TODO: Implement this.
    return {"result": "Status."}


@app.post("dske/api/v1/key-share")
async def post_key_share():
    """
    API: Post key share.
    """
    # TODO: Implement this.
    return {"result": "Post key-share result."}
