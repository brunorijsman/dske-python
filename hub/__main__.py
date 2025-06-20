"""
Main module for a DSKE security hub.
"""

import argparse
import os
import signal
import fastapi
import pydantic
import uvicorn
from common import configuration
from common import utils
from common.block import APIBlock
from common.share import APIShare
from .hub import Hub


def parse_command_line_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="DSKE Hub")
    parser.add_argument("name", type=str, help="Hub name")
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=configuration.DEFAULT_BASE_PORT,
        help="Port number",
    )
    args = parser.parse_args()
    return args


_ARGS = parse_command_line_arguments()
# TODO: Make pre-shared key size configurable.
_HUB = Hub(_ARGS.name, pre_shared_key_size=32)
_APP = fastapi.FastAPI()


# This should be a POST instead of a GET
@_APP.get(f"/hub/{_HUB.name}/dske/oob/v1/register-client")
async def get_oob_register_client(client_name: str):
    """
    DSKE Out of band: Register a client.
    """
    peer_client = _HUB.register_peer_client(client_name)
    # TODO: Return a proper error when there is an exception because the client already is
    #       peer.
    return {
        "hub_name": _HUB.name,
        "pre_shared_key": utils.bytes_to_str(peer_client.pre_shared_key),
    }


@_APP.get(f"/hub/{_HUB.name}/dske/oob/v1/psrd")
async def get_oob_psrd(client_name: str, size: pydantic.PositiveInt) -> APIBlock:
    """
    DSKE Out of band: Get a block of Pre-Shared Random Data (PSRD).
    """
    # TODO: Error if the client was not peer.
    # TODO: Allow size to be None (use default size decided by hub).
    block = _HUB.generate_block_for_peer_client(client_name, size)
    return block.to_api()


@_APP.post(f"/hub/{_HUB.name}/dske/api/v1/key-share")
async def post_key_share(api_share: APIShare):
    """
    DSKE API: Post key share.
    """
    print(f"Received POST /dske/hub/api/v1/key-share {api_share=}", flush=True)
    _HUB.store_share_received_from_client(api_share)


@_APP.get(f"/hub/{_HUB.name}/dske/api/v1/key-share")
async def get_key_share(client_name: str, key_id: str) -> APIShare:
    """
    DSKE API: Get key share.
    """
    print(
        f"Received POST /dske/hub/api/v1/key-share {client_name=} {key_id=}", flush=True
    )
    return _HUB.get_share_requested_by_client(client_name, key_id)


@_APP.get(f"/hub/{_HUB.name}/mgmt/v1/status")
async def get_mgmt_status():
    """
    Management: Get status.
    """
    status = _HUB.to_mgmt()
    return status


@_APP.post(f"/hub/{_HUB.name}/mgmt/v1/stop")
async def post_mgmt_stop():
    """
    Management: Post stop.
    """
    # TODO: Can we delete the PID file later, when the process actually terminates?
    utils.delete_pid_file("hub", _HUB.name)
    os.kill(os.getpid(), signal.SIGTERM)
    # TODO: Does this result actually get returned
    return {"result": "Hub stopped"}


def main():
    """
    Main entry point for the hub package.
    """
    utils.create_pid_file("hub", _HUB.name)
    config = uvicorn.Config(app=_APP, port=_ARGS.port)
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()
