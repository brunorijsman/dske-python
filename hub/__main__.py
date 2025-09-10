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
from common.share_api import APIGetShareResponse, APIPostShareRequest
from common.registration_api import APIPutRegistrationRequest
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
_HUB = Hub(_ARGS.name)
_APP = fastapi.FastAPI()


@_APP.put(f"/hub/{_HUB.name}/dske/oob/v1/registration")
async def put_oob_client_registration(
    registration_request: APIPutRegistrationRequest,
):
    """
    DSKE Out of band: Register a client.
    """
    _peer_client = _HUB.register_client(client_name=registration_request.client_name)
    return {"hub_name": _HUB.name}


@_APP.get(f"/hub/{_HUB.name}/dske/oob/v1/psrd")
async def get_oob_psrd(
    client_name: str,
    pool_owner: str,
    size: pydantic.PositiveInt,
) -> APIBlock:
    """
    DSKE Out of band: Get a block of Pre-Shared Random Data (PSRD).
    """
    # TODO: Error if the client was not peer.
    # TODO: Allow size to be None (use default size decided by hub).
    block = _HUB.generate_block_for_client(client_name, pool_owner, size)
    return block.to_api()


@_APP.post(f"/hub/{_HUB.name}/dske/api/v1/key-share")
async def post_key_share(api_post_share_request: APIPostShareRequest):
    """
    DSKE API: Post key share.
    """
    _HUB.store_share_received_from_client(api_post_share_request)


@_APP.get(f"/hub/{_HUB.name}/dske/api/v1/key-share")
async def get_key_share(client_name: str, key_id: str) -> APIGetShareResponse:
    """
    DSKE API: Get key share.
    """
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
