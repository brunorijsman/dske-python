"""
Command line interface for DSKE client.
"""

import argparse
from common import configuration


def _check_start_request_psrd_threshold(value):
    int_value = int(value)
    if (
        int_value <= configuration.MIN_START_REQUEST_PSRD_THRESHOLD
        or int_value > configuration.MAX_START_REQUEST_PSRD_THRESHOLD
    ):
        raise argparse.ArgumentTypeError(
            f"value {value} is invalid; "
            f"it must be between "
            f"{configuration.MIN_START_REQUEST_PSRD_THRESHOLD} and "
            f"{configuration.MAX_START_REQUEST_PSRD_THRESHOLD}"
        )
    return int_value


def _check_get_psrd_block_size(value):
    int_value = int(value)
    if (
        int_value <= configuration.MIN_GET_PSRD_BLOCK_SIZE
        or int_value > configuration.MAX_GET_PSRD_BLOCK_SIZE
    ):
        raise argparse.ArgumentTypeError(
            f"value {value} is invalid; "
            f"it must be between "
            f"{configuration.MIN_GET_PSRD_BLOCK_SIZE} and "
            f"{configuration.MAX_GET_PSRD_BLOCK_SIZE}"
        )
    return int_value


def _check_stop_request_psrd_threshold(value):
    int_value = int(value)
    if (
        int_value <= configuration.MIN_STOP_REQUEST_PSRD_THRESHOLD
        or int_value > configuration.MAX_STOP_REQUEST_PSRD_THRESHOLD
    ):
        raise argparse.ArgumentTypeError(
            f"value {value} is invalid; "
            f"it must be between "
            f"{configuration.MIN_STOP_REQUEST_PSRD_THRESHOLD} and "
            f"{configuration.MAX_STOP_REQUEST_PSRD_THRESHOLD}"
        )
    return int_value


def _check_min_nr_shares(value):
    int_value = int(value)
    if (
        int_value <= configuration.MIN_MIN_NR_SHARES
        or int_value > configuration.MAX_MIN_NR_SHARES
    ):
        raise argparse.ArgumentTypeError(
            f"value {value} is invalid; "
            f"it must be between "
            f"{configuration.MIN_MIN_NR_SHARES} and "
            f"{configuration.MAX_MIN_NR_SHARES}"
        )
    return int_value


def parse_command_line_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="DSKE Client", prog="client")
    parser.add_argument("name", type=str, help="Client name")
    parser.add_argument(
        "--port",
        type=int,
        help="Port number",
    )
    parser.add_argument(
        "--start-request-psrd_threshold",
        type=_check_start_request_psrd_threshold,
        default=configuration.DEFAULT_START_REQUEST_PSRD_THRESHOLD,
        help=(
            f"Start request PSRD threshold "
            f"(default: {configuration.DEFAULT_START_REQUEST_PSRD_THRESHOLD})"
        ),
    )
    parser.add_argument(
        "--stop-request-psrd-threshold",
        type=_check_start_request_psrd_threshold,
        default=configuration.DEFAULT_STOP_REQUEST_PSRD_THRESHOLD,
        help=(
            f"Stop request PSRD threshold "
            f"(default: {configuration.DEFAULT_STOP_REQUEST_PSRD_THRESHOLD})"
        ),
    )
    parser.add_argument(
        "--get-psrd-block-size",
        type=_check_get_psrd_block_size,
        default=configuration.DEFAULT_GET_PSRD_BLOCK_SIZE,
        help=(
            f"Request PSRD block size "
            f"(default: {configuration.DEFAULT_GET_PSRD_BLOCK_SIZE})"
        ),
    )
    parser.add_argument(
        "--min-nr-shares",
        type=_check_min_nr_shares,
        default=configuration.DEFAULT_MIN_NR_SHARES,
        help=(
            f"Minimum number of shares "
            f"(default: {configuration.DEFAULT_MIN_NR_SHARES})"
        ),
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
