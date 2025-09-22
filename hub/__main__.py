"""
Main module for a DSKE security hub.
"""

import argparse
import os
import signal
import sys
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


@_APP.middleware("http")
async def dske_authentication(request: fastapi.Request, call_next):
    """
    Check the DSKE authentication header in the request. Add the DSKE authentication header to the
    response.
    """
    authenticate = "/dske/api/" in request.url.path
    if authenticate:
        error_message = await verify_signature_in_request(request)
        if error_message is not None:
            return fastapi.Response(
                content=error_message, status_code=fastapi.status.HTTP_403_FORBIDDEN
            )
    response = await call_next(request)
    if authenticate:
        response = await add_signature_to_response(response)
    return response


async def verify_signature_in_request(request: fastapi.Request) -> str | None:
    """
    Verify the signature in the request. Returns None if the signature is valid. Returns and error
    message if the signature is invalid.
    """
    body = await request.body()
    params = request.scope.get("query_string", b"")
    print(f"Middleware: TODO validate signature {body=} {params=}", file=sys.stderr)
    # TODO implement this
    return None


async def add_signature_to_response(response: fastapi.Response):
    """
    Add a signature to the response.
    """
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    content = b"".join(chunks)
    print(f"Middleware: TODO add signature {content=}", file=sys.stderr)
    response = fastapi.Response(
        content=content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )
    return response


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
async def post_key_share(
    api_post_share_request: APIPostShareRequest, response: fastapi.Response
):
    """
    DSKE API: Post key share.
    """
    # TODO: Validate authentication header in request
    # TODO: Add authentication header to response
    _HUB.store_share_received_from_client(api_post_share_request)
    response.headers["DSKE-Authentication"] = "TODO 1"


@_APP.get(f"/hub/{_HUB.name}/dske/api/v1/key-share")
async def get_key_share(client_name: str, key_id: str) -> APIGetShareResponse:
    """
    DSKE API: Get key share.
    """
    # TODO: Validate authentication header in request
    # TODO: Add authentication header to response
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
