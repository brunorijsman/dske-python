"""
Main module for a DSKE client.
"""

import argparse
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
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port number")
    args = parser.parse_args()
    return args


_ARGS = parse_command_line_arguments()
_CLIENT_NAME = _ARGS.name
_CLIENT = Client(_CLIENT_NAME)
_APP = fastapi.FastAPI()


@_APP.post("/dske-client/mgmt/v1/stop")
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
