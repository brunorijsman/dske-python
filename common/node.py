"""
A node (i.e. a hub or a client).
"""

import dataclasses
import enum


class NodeType(enum.Enum):
    """
    The type of node.
    """

    HUB = 1
    CLIENT = 2


@dataclasses.dataclass
class Node:
    """
    A node (i.e. a hub or a client).
    """

    type: NodeType
    name: str
    port: None | int = None
    url: None | str = None
