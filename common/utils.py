"""
Common functions for the project.
"""

import base64
import os
import sys
import pathlib


def bytes_to_str(data: bytes | None, truncate: bool = False) -> str | None:
    """
    Convert bytes to a base64-encoded string. But None gets converted to None.
    """
    if data is None:
        return None
    max_length = 10
    if len(data) > max_length and truncate:
        data = data[0:max_length]
        add_ellipsis = True
    else:
        add_ellipsis = False
    string = base64.b64encode(data).decode("utf-8")
    if add_ellipsis:
        string += "..."
    return string


def str_to_bytes(string: str | None) -> bytes | None:
    """
    Convert a base64-encoded string to bytes. But None gets converted to None.
    """
    if string is None:
        return None
    return base64.b64decode(string)


def to_mgmt(obj: object) -> dict | None:
    """
    Get the management status.
    """
    if obj is None:
        return None
    return obj.to_mgmt()


def pid_file_name(node_type: str, node_name: str) -> str:
    """
    The name of the file that is used to store the process ID.
    """
    # TODO: Use a better choice for the temp directory than /tmp
    return f"/tmp/dske-{node_type}-{node_name}.pid"


def create_pid_file(node_type: str, node_name: str) -> None:
    """
    Write a process ID file for the node.
    """
    file_name = pid_file_name(node_type, node_name)
    if pid_file_exists(node_type, node_name):
        print(f"Warning: overwriting existing PID file {file_name}", file=sys.stderr)
    with open(file_name, "w", encoding="utf-8") as pid_file:
        pid_file.write(f"{os.getpid()}\n")


def delete_pid_file(node_type: str, node_name: str) -> None:
    """
    Delete the process ID file for the node.
    """
    # TODO: Make this a WARNING log message
    os.remove(pid_file_name(node_type, node_name))


def pid_file_exists(node_type: str, node_name: str) -> bool:
    """
    Does a process ID file for the node exist?
    """
    path = pathlib.Path(pid_file_name(node_type, node_name))
    return path.exists()
