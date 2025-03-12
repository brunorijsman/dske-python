"""
Main module for a DSKE security hub.
"""

import argparse
import os
import signal

import fastapi
import pydantic
import uvicorn

import common

from . import api
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


# This should be a POST instead of a GET
@_APP.get("/dske/hub/oob/v1/register-client")
async def get_oob_register_dske_client(client_name: str):
    """
    Out of band: Register a DSKE client.
    """
    peer_client = _HUB.register_peer_client(client_name)
    # TODO: Return a proper error when there is an exception because the client already is
    #       peer.
    return {
        "hub_name": _HUB_NAME,
        "pre_shared_key": common.bytes_to_str(peer_client.pre_shared_key),
    }


@_APP.get("/dske/hub/oob/v1/psrd")
async def get_oob_psrd(client_name: str, size: pydantic.PositiveInt):
    """
    Out of band: Get a block of Pre-Shared Random Data (PSRD).
    """
    # TODO: Error if the client was not peer.
    # TODO: Allow size to be None (use default size decided by hub).
    psrd_block = _HUB.generate_psrd_block_for_peer_client(client_name, size)
    return psrd_block.to_api_dict()


@_APP.post("/dske/hub/api/v1/key-share")
async def post_api_key_share(_key_share: api.APIKeyShare):
    """
    API: Post key share.
    """
    print(f"Received POST /dske/hub/api/v1/key-share {_key_share=}", flush=True)
    # TODO: Implement this.
    return {"result": "Post key-share result."}


@_APP.get("/dske/hub/mgmt/v1/status")
async def get_mgmt_status():
    """
    Management: Get status.
    """
    status = _HUB.to_mgmt_dict()
    return status


@_APP.post("/dske/hub/mgmt/v1/stop")
async def post_mgmt_stop():
    """
    Management: Post stop.
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
