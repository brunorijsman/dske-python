"""
A node (i.e. a hub or a client).
"""

import errno
import dataclasses
import enum
import socket


class NodeType(enum.IntEnum):
    """
    The type of node.
    """

    HUB = 1
    CLIENT = 2

    def __str__(self):
        """
        Return the string representation of the node type.
        """
        return self.name.lower()

    @staticmethod
    def from_str(label: str) -> "NodeType":
        """
        Convert a string to a NodeType.
        """
        label = label.lower()
        if label == "hub":
            return NodeType.HUB
        if label == "client":
            return NodeType.CLIENT
        raise ValueError(f"Unknown node type: {label}")


@dataclasses.dataclass(order=True)
class Node:
    """
    A node (i.e. a hub or a client).
    Nodes are ordered by type and name.
    """

    type: NodeType
    name: str
    encryptor_names: list[str]  # Only relevant for clients, empty list for hubs
    port: None | int = None
    base_url: None | str = None

    def is_started(self) -> bool:
        """
        Check if the node has been started and is ready to accept API calls.
        """
        return self.is_port_in_use()

    def is_stopped(self) -> bool:
        """
        Check if the node has been stopped and is ready to be restarted.
        """
        return not self.is_port_in_use()

    def is_port_in_use(self) -> bool:
        """
        Is the TCP port already in use by some process (might not be a DSKE node, but nevertheless
        it means the DSKE node cannot be started on that port)?
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("", self.port))
        except OSError as error:
            if error.errno == errno.EADDRINUSE:
                return True
            return False
        sock.close()
        return False
