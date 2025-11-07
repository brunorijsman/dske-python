"""
Command line interface for DSKE hub.
"""

import argparse
from common import configuration


def _check_share_timeout_secs(value):
    int_value = int(value)
    if (
        int_value <= configuration.MIN_SHARE_TIMEOUT_SECS
        or int_value > configuration.MAX_SHARE_TIMEOUT_SECS
    ):
        raise argparse.ArgumentTypeError(
            f"value {value} is invalid; "
            f"it must be between "
            f"{configuration.MIN_SHARE_TIMEOUT_SECS} and "
            f"{configuration.MAX_SHARE_TIMEOUT_SECS}"
        )
    return int_value


def parse_command_line_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="DSKE Hub", prog="hub")
    parser.add_argument("name", type=str, help="Hub name")
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Port number",
    )
    parser.add_argument(
        "--share-timeout-secs",
        type=_check_share_timeout_secs,
        default=configuration.DEFAULT_SHARE_TIMEOUT_SECS,
        help=(
            f"Share timeout in seconds "
            f"(default: {configuration.DEFAULT_SHARE_TIMEOUT_SECS})"
        ),
    )

    args = parser.parse_args()
    return args
