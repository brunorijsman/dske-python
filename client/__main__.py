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
_CLIENT = Client(_ARGS.name, _ARGS.hubs)


@contextlib.asynccontextmanager
async def lifespan(_app: fastapi.FastAPI):
    """
    Lifespan manager for the FastAPI app.
    """
    await _CLIENT.register_all_hubs()
    yield
    await _CLIENT.unregister_all_hubs()


_APP = fastapi.FastAPI(lifespan=lifespan)


@_APP.post("/dske/client/mgmt/v1/stop")
async def mgmt_stop():
    """
    Management: Stop.
    """
    os.kill(os.getpid(), signal.SIGTERM)
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
