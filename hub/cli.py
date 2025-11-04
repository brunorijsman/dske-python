"""
Command line interface for DSKE hub.
"""

import argparse


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
    args = parser.parse_args()
    return args
