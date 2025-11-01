"""
Configuration for a DSKE topology.
"""

import pprint
import sys
import cerberus
import yaml
from common.node import Node, NodeType

DEFAULT_BASE_PORT = 8100
DEFAULT_CONFIGURATION_FILE = "topology.yaml"


class Configuration:
    """
    Configuration for a DSKE topology.
    """

    _nodes: list[Node]

    def __init__(self, nodes, base_port=DEFAULT_BASE_PORT):
        # Sort nodes by type and name, so that clients are always before hubs (the order matters
        # for startup and shutdown).
        self._nodes = sorted(nodes)
        self._base_port = base_port
        self._assign_ports_and_urls()

    @property
    def nodes(self):
        """
        Return the nodes.
        """
        return self._nodes

    def _assign_ports_and_urls(self):
        """
        Assign port numbers and URLs to the nodes.
        """
        port = self._base_port
        for node in self._nodes:
            node.port = port
            node.base_url = f"http://127.0.0.1:{port}/{node.type}/{node.name}"
            port += 1


def parse_configuration_file(filename: str = DEFAULT_CONFIGURATION_FILE):
    """
    Parse the configuration file.
    """
    hub_schema = {
        "type": "dict",
        "schema": {
            "name": {"type": "string"},
        },
    }
    encryptor_schema = {
        "type": "dict",
        "schema": {
            "name": {"type": "string"},
        },
    }
    client_schema = {
        "type": "dict",
        "schema": {
            "name": {"type": "string"},
            "encryptors": {"type": "list", "schema": encryptor_schema},
        },
    }
    schema = {
        "hubs": {"type": "list", "schema": hub_schema},
        "clients": {"type": "list", "schema": client_schema},
    }
    try:
        with open(filename, "r", encoding="utf-8") as file:
            try:
                parsed_config = yaml.safe_load(file)
            except yaml.YAMLError as err:
                print(
                    f"Could not load configuration file {filename}: {str(err)}",
                    file=sys.stderr,
                )
                sys.exit(1)
    except (OSError, IOError) as err:
        print(f"Could not open configuration file {filename} ({err})", file=sys.stderr)
        sys.exit(1)
    validator = cerberus.Validator()
    if not validator.validate(parsed_config, schema):
        print(f"Could not parse configuration file {filename}", file=sys.stderr)
        pretty_printer = pprint.PrettyPrinter()
        pretty_printer.pprint(validator.errors)
        sys.exit(1)
    parsed_config = validator.normalized(parsed_config)
    nodes = []
    for parsed_hub_config in parsed_config["hubs"]:
        node = Node(NodeType.HUB, parsed_hub_config["name"])
        nodes.append(node)
    for parsed_client_config in parsed_config["clients"]:
        node = Node(NodeType.CLIENT, parsed_client_config["name"])
        nodes.append(node)
    return Configuration(nodes)
