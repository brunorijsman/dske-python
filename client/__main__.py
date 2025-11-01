"""
Main module for a DSKE client.
"""

import argparse
import contextlib
import os
import signal
from typing import Annotated
import fastapi
import uvicorn
from common import configuration
from common import utils
from common.exceptions import DSKEException, EncryptorNotRegisteredForClientError
from .client import Client


def parse_command_line_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="DSKE Client")
    parser.add_argument("name", type=str, help="Client name")
    parser.add_argument(
        "--port", type=int, default=configuration.DEFAULT_BASE_PORT, help="Port number"
    )
    parser.add_argument(
        "--hubs",
        nargs="+",
        type=str,
        help=f"Base URLs for hubs (e.g., http://127.0.0.1:{configuration.DEFAULT_BASE_PORT})",
    )
    parser.add_argument(
        "--encryptors",
        nargs="+",
        type=str,
        help="Names (SAE IDs) of encryptors consuming keys from this client (KME).",
    )
    args = parser.parse_args()
    return args


_ARGS = parse_command_line_arguments()
peer_hub_urls = _ARGS.hubs
if peer_hub_urls is None:
    peer_hub_urls = []
_CLIENT = Client(_ARGS.name, _ARGS.encryptors, peer_hub_urls)


@contextlib.asynccontextmanager
async def lifespan(_app: fastapi.FastAPI):
    """
    Do the things that need to be done just after startup and just before shutdown.
    """
    _CLIENT.start_all_peer_hubs()
    yield
    # We currently do not have any shutdown actions.


_APP = fastapi.FastAPI(lifespan=lifespan)


@_APP.exception_handler(DSKEException)
async def dske_exception_handler(_request: fastapi.Request, exc: DSKEException):
    """
    Handle DSKE exceptions.
    """
    return fastapi.responses.JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "details": exc.details},
    )


@_APP.get(f"/client/{_CLIENT.name}/etsi/api/v1/keys/{{slave_sae_id}}/status")
async def get_etsi_status(
    slave_sae_id: str,
    authorization_header: Annotated[str | None, fastapi.Header()] = None,
):
    """
    ETSI QKD 014 API: Status.
    """
    master_sae_id = calling_sae_id(authorization_header)
    return await _CLIENT.etsi_status(master_sae_id, slave_sae_id)


@_APP.get(f"/client/{_CLIENT.name}/etsi/api/v1/keys/{{slave_sae_id}}/enc_keys")
async def get_etsi_get_key(
    slave_sae_id: str,
    size: int | None = None,
    authorization_header: Annotated[str | None, fastapi.Header()] = None,
):
    """
    ETSI QKD 014 API: Get Key.
    """
    master_sae_id = calling_sae_id(authorization_header)
    return await _CLIENT.etsi_get_key(master_sae_id, slave_sae_id, size)


@_APP.get(f"/client/{_CLIENT.name}/etsi/api/v1/keys/{{master_sae_id}}/dec_keys")
async def get_eti_get_key_with_key_ids(
    master_sae_id: str,
    key_ID: str,
    authorization_header: Annotated[str | None, fastapi.Header()] = None,
):
    """
    ETSI QKD 014 API: Get Key with Key IDs.
    """
    # ETSI QKD 014 says that ID in key_ID has to be upper case, which lint doesn't like.
    # pylint: disable=invalid-name
    slave_sae_id = calling_sae_id(authorization_header)
    return await _CLIENT.etsi_get_key_with_key_ids(master_sae_id, slave_sae_id, key_ID)


@_APP.get(f"/client/{_CLIENT.name}/mgmt/v1/status")
async def get_mgmt_status():
    """
    Management: Get status.
    """
    return _CLIENT.to_mgmt()


@_APP.post(f"/client/{_CLIENT.name}/mgmt/v1/stop")
async def post_mgmt_stop():
    """
    Management: Post stop.
    """
    utils.delete_pid_file("client", _CLIENT.name)
    os.kill(os.getpid(), signal.SIGTERM)
    return {"result": "Client stopped"}


def calling_sae_id(authorization_header: str | None) -> str:
    """
    Get the SAE ID of the calling entity from the request headers.
    """
    if authorization_header is None:
        if len(_CLIENT.encryptor_names) == 1:
            # If the client has exactly one encryptor, we assume that this is the one.
            # This makes it easier for users to use curl for testing in simple topologies.
            master_sae_id = _CLIENT.encryptor_names[0]
        else:
            # There is more than one encryptor, so we cannot guess which one is calling.
            raise EncryptorNotRegisteredForClientError(
                client_name=_CLIENT.name,
                encryptor_name=authorization_header,
            )
    else:
        master_sae_id = authorization_header.strip()
    return master_sae_id


def main():
    """
    Main entry point for the hub package.
    """
    utils.create_pid_file("client", _CLIENT.name)
    config = uvicorn.Config(app=_APP, port=_ARGS.port)
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()
