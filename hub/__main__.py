"""
Main module for a DSKE security hub.
"""

import argparse
import base64
import os
import signal

import fastapi
import pydantic
import uvicorn

from .hub import Hub


def parse_command_line_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="DSKE Hub")
    parser.add_argument("name", type=str, help="Hub name")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port number")
    args = parser.parse_args()
    return args


_ARGS = parse_command_line_arguments()
_HUB_NAME = _ARGS.name
# TODO: Make pre-shared key size configurable.
_HUB = Hub(_HUB_NAME, pre_shared_key_size=32)
_APP = fastapi.FastAPI()


@_APP.get("/dske/hub/oob/v1/register-client")
async def oob_get_register_dske_client(client_name: str):
    """
    Out of band: Register a DSKE client.
    """
    peer_client = _HUB.register_peer_client(client_name)
    encoded_pre_shared_key = base64.b64encode(peer_client.pre_shared_key).decode(
        "utf-8"
    )
    # TODO: Return a proper error when there is an exception because the client already is
    #       peer.
    return {"hub_name": _HUB_NAME, "pre_shared_key": encoded_pre_shared_key}


@_APP.get("/dske/hub/oob/v1/psrd")
async def oob_get_psrd(size: pydantic.PositiveInt):
    """
    Out of band: Get Pre-Shared Random Data (PSRD).
    """
    # TODO: Add dske_client_name. Note: we don't do authentication of out-of-band requests.
    # TODO: Add dske_client_name parameter to create_random_psrd.
    # TODO: Error if the client was not peer.
    _psrd = _HUB.create_random_psrd(size)
    return {"result": "Pre-shared random data."}


@_APP.get("/dske/hub/api/v1/status")
async def api_get_status():
    """
    API: Get status.
    """
    # TODO: Implement this.
    return {"result": "Status."}


@_APP.post("/dske/hub/api/v1/key-share")
async def api_post_key_share():
    """
    API: Post key share.
    """
    # TODO: Implement this.
    return {"result": "Post key-share result."}


@_APP.post("/dske/hub/mgmt/v1/stop")
async def mgmt_stop():
    """
    Management: Stop.
    """
    os.kill(os.getpid(), signal.SIGTERM)
    return {"result": "Hub stopped"}


def main():
    """
    Main entry point for the hub package.
    """
    config = uvicorn.Config(app=_APP, port=_ARGS.port)
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()
