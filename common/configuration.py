"""
Configuration for a DSKE topology.
"""

import pprint
import sys

import cerberus
import yaml

DEFAULT_BASE_PORT = 8100
DEFAULT_CONFIGURATION_FILE = "topology.yaml"


class Configuration:
    """
    Configuration for a DSKE topology.
    """

    def __init__(self, nodes, base_port=DEFAULT_BASE_PORT):
        self._nodes = nodes
        self._base_port = base_port
        self._port_assignments = {}
        self._assign_ports()

    @property
    def nodes(self):
        """
        Return the nodes.
        """
        return self._nodes

    @property
    def port_assignments(self):
        """
        Return the port assignments.
        """
        return self._port_assignments

    def node_port(self, node_type: str, node_name: str) -> int:
        """
        Return the TCP port number assigned to a node.
        """
        return self._port_assignments[(node_type, node_name)]

    def _assign_ports(self):
        """
        Assign port numbers to the nodes.
        """
        port = self._base_port
        for node_type, node_name in self._nodes:
            self._port_assignments[(node_type, node_name)] = port
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
    client_schema = {
        "type": "dict",
        "schema": {
            "name": {"type": "string"},
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
        nodes.append(("hub", parsed_hub_config["name"]))
    for parsed_client_config in parsed_config["clients"]:
        nodes.append(("client", parsed_client_config["name"]))
    return Configuration(nodes)
