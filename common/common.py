"""
Common functions for the project.
"""

import base64


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


def to_mgmt_dict(obj: object) -> dict | None:
    """
    Return the management status of an object. But None gets converted to None.
    """
    if obj is None:
        return None
    return obj.to_mgmt_dict()


def to_protocol_dict(obj: object) -> dict | None:
    """
    Return the encoding for the object as used in the DSKE protocol.
    """
    if obj is None:
        return None
    return obj.to_protocol_dict()
