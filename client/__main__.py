"""
Main module for a DSKE client.
"""

import argparse
import contextlib
import os
import signal

import fastapi
import uvicorn

from .client import Client


def parse_command_line_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="DSKE Client")
    parser.add_argument("name", type=str, help="Client name")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument(
        "--hubs",
        nargs="+",
        type=str,
        help="Base URLs for hubs (e.g., http://localhost:8000)",
    )
    args = parser.parse_args()
    return args


_ARGS = parse_command_line_arguments()
peer_hub_urls = _ARGS.hubs
if peer_hub_urls is None:
    peer_hub_urls = []
_CLIENT = Client(_ARGS.name, peer_hub_urls)


@contextlib.asynccontextmanager
async def lifespan(_app: fastapi.FastAPI):
    """
    Lifespan manager for the FastAPI app.
    """
    # TODO: We need a formal Finite State Machine (FSM) for each peer hub, running independently
    #       from the FSMs of other peer hubs.
    await _CLIENT.register_with_all_peer_hubs()
    # TODO: For now, we just request one block of PSRD from each peer hub. Once we have FSMs,
    #       we need to request new blocks of PSRD as the random data is consumed and falls below
    #       some defined threshold.
    await _CLIENT.request_psrd_from_all_peer_hubs()
    yield
    await _CLIENT.unregister_from_all_peer_hubs()


_APP = fastapi.FastAPI(lifespan=lifespan)


@_APP.get("/dske/client/etsi/api/v1/keys/{slave_sae_id}/status")
async def api_get_etsi_status(slave_sae_id: str):
    """
    ETSI QKD 014 API: Status.
    """
    return _CLIENT.etsi_status(slave_sae_id)


@_APP.get("/dske/client/etsi/api/v1/keys/{slave_sae_id}/enc_keys")
async def api_get_etsi_get_key(slave_sae_id: str):
    """
    ETSI QKD 014 API: Get Key.
    """
    return _CLIENT.etsi_get_key(slave_sae_id)


@_APP.get("/dske/client/etsi/api/v1/keys/{slave_sae_id}/dec_keys")
async def api_get_etsi_get_key_with_key_ids(slave_sae_id: str, key_ID: str):
    """
    ETSI QKD 014 API: Get Key with Key IDs.
    """
    return _CLIENT.etsi_get_key_with_key_ids(slave_sae_id, key_id=key_ID)


@_APP.get("/dske/client/mgmt/v1/status")
async def mgmt_():
    """
    Management: Get status.
    """
    return _CLIENT.to_management_json()


@_APP.post("/dske/client/mgmt/v1/stop")
async def mgmt_post_stop():
    """
    Management: Post stop.
    """
    os.kill(os.getpid(), signal.SIGTERM)
    # TODO: Better result
    return {"result": "Client stopped"}


def main():
    """
    Main entry point for the hub package.
    """
    config = uvicorn.Config(app=_APP, port=_ARGS.port)
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()
