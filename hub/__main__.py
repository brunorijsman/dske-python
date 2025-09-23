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
from common.signature import Signature
from common.signing_key import MiddlewareSigningKey
from common.registration_api import (
    APIPutRegistrationRequest,
    APIPutRegistrationResponse,
)
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
    # Authentication is only done for DSKE in-band protocol messages. Checking the URL path is
    # an ugly way of achieving this. Mounting sub-applications would have been cleaner, but then
    # we would get a separate OpenAPI docs page for each sub-application.
    authenticate = "/dske/api/" in request.url.path
    if authenticate:
        await middleware_check_request_signature(request)
    response = await call_next(request)
    if authenticate:
        response = await middleware_add_response_signature(response)
    return response


async def middleware_check_request_signature(request: fastapi.Request):
    """
    Verify the signature in the request. Returns None if the signature is valid. Returns and error
    message if the signature is invalid.
    """
    _signature = Signature.from_headers(request.headers)
    # TODO: $$$ continue from here, finish this: we need to allocate the signing key from the pool
    #       which we cannot do here; we need to know the peer pool first.
    #
    # Maybe pass a "raw_request: fastapi.Request" object to the @app.xxx handler
    # and extract the header and the raw body there?
    #
    # body = await request.body()
    # params = request.scope.get("query_string", None)
    # # TODO: $$$ Continue from here
    # signature_header_name = InternalKey.SIGNING_KEY_HEADER_NAME
    # signature_header_value = headers.pop(signature_header_name.lower(), None)
    # # TODO check that signature is correct value
    # print(
    #     f"middleware_check_request_signature: {signature_header_value=}",
    #     file=sys.stderr,
    # )
    # TODO: If the check fails (e.g. header is missing), throw an exception which leads to a
    #       403 FORBIDDEN response.


async def middleware_add_response_signature(
    response: fastapi.Response,
) -> fastapi.Response:
    """
    Add a signature to the response.
    """
    signing_key = MiddlewareSigningKey.extract_from_headers(response.headers)
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    content = b"".join(chunks)
    signature = signing_key.sign(content)
    signature.add_to_headers(response.headers)
    signed_response = fastapi.Response(
        content=content,
        status_code=response.status_code,
        headers=response.headers,
        media_type=response.media_type,
    )
    return signed_response


@_APP.put(f"/hub/{_HUB.name}/dske/oob/v1/registration")
async def put_oob_client_registration(
    registration_request: APIPutRegistrationRequest,
) -> APIPutRegistrationResponse:
    """
    DSKE Out of band: Register a client.
    """
    _peer_client = _HUB.register_client(client_name=registration_request.client_name)
    response = APIPutRegistrationResponse(hub_name=_HUB.name)
    return response


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
    api_post_share_request: APIPostShareRequest,
    headers_temp_response: fastapi.Response,
):
    """
    DSKE API: Post key share.
    """
    _HUB.store_share_received_from_client(api_post_share_request, headers_temp_response)


@_APP.get(f"/hub/{_HUB.name}/dske/api/v1/key-share")
async def get_key_share(
    client_name: str,
    key_id: str,
    headers_temp_response: fastapi.Response,
) -> APIGetShareResponse:
    """
    DSKE API: Get key share.
    """
    headers_temp_response = _HUB.get_share_requested_by_client(
        client_name, key_id, headers_temp_response
    )
    return headers_temp_response


# TODO: Add -> return type, here and everywhere
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
