"""
Configuration for DSKE manager.
"""

import pprint
import sys
import cerberus
import yaml
from common.node import Node, NodeType

DEFAULT_BASE_PORT = 8100
"""
Default base port for DSKE nodes. First hub uses this port, second hub uses this port + 1, and so
on. Clients use ports after all hubs.
"""

# In real life, the thresholds and the block size defined below would be much larger, perhaps
# gigabytes. For testing purposes, we use much smaller values.

# Start requesting more PSRD blocks from the hub when the amount of PSRD in the pool falls below
# this threshold.
DEFAULT_START_REQUEST_PSRD_THRESHOLD = 500
MIN_START_REQUEST_PSRD_THRESHOLD = 1
MAX_START_REQUEST_PSRD_THRESHOLD = 10_000_000_000

# Stop requesting more PSRD blocks from the hub when the amount of PSRD in the pool rises above or
# equal to this threshold.
DEFAULT_STOP_REQUEST_PSRD_THRESHOLD = 2000
MIN_STOP_REQUEST_PSRD_THRESHOLD = 1
MAX_STOP_REQUEST_PSRD_THRESHOLD = 10_000_000_000

# When requesting more PSRD blocks from the hub, request blocks of this size.
DEFAULT_GET_PSRD_BLOCK_SIZE = 2000
MIN_GET_PSRD_BLOCK_SIZE = 1
MAX_GET_PSRD_BLOCK_SIZE = 10_000_000

# Minimum number of shares needed to reconstruct a a key from the key shares using Shamir's Secret
# Sharing (SSS).
DEFAULT_MIN_NR_SHARES = 3
MIN_MIN_NR_SHARES = 1  # We allow 1, which really means the secret is not split at all.
MAX_MIN_NR_SHARES = 128


def fatal_error(message: str):
    """
    Print a fatal error message and exit.
    """
    print(message, file=sys.stderr)
    sys.exit(1)


class Configuration:
    """
    Configuration for the DSKE manager.
    """

    nodes: list[Node]
    base_port: int
    start_request_psrd_threshold: int
    stop_request_psrd_threshold: int
    get_psrd_block_size: int
    min_nr_shares: int

    def __init__(
        self,
        base_port,
        start_request_psrd_threshold,
        stop_request_psrd_threshold,
        get_psrd_block_size,
        min_nr_shares,
        nodes,
    ):
        self.base_port = base_port
        self.start_request_psrd_threshold = start_request_psrd_threshold
        self.stop_request_psrd_threshold = stop_request_psrd_threshold
        self.get_psrd_block_size = get_psrd_block_size
        self.min_nr_shares = min_nr_shares
        # Sort nodes by type and name, so that clients are always before hubs (the order matters
        # for startup and shutdown).
        self.nodes = sorted(nodes)
        self._assign_ports_and_urls()

    def _assign_ports_and_urls(self):
        """
        Assign port numbers and URLs to the nodes.
        """
        port = self.base_port
        for node in self.nodes:
            node.port = port
            node.base_url = f"http://127.0.0.1:{port}/{node.type}/{node.name}"
            port += 1


HUB_SCHEMA = {
    "type": "dict",
    "schema": {
        "name": {"type": "string"},
    },
}

ENCRYPTOR_SCHEMA = {
    "type": "dict",
    "schema": {
        "name": {"type": "string"},
    },
}

CLIENT_SCHEMA = {
    "type": "dict",
    "schema": {
        "name": {"type": "string"},
        "encryptors": {"type": "list", "schema": ENCRYPTOR_SCHEMA, "default": []},
    },
}

SCHEMA = {
    "base_port": {
        "type": "integer",
        "default": DEFAULT_BASE_PORT,
        "min": 1,
        "max": 65535,
    },
    "start_request_psrd_threshold": {
        "type": "integer",
        "default": DEFAULT_START_REQUEST_PSRD_THRESHOLD,
        "min": MIN_START_REQUEST_PSRD_THRESHOLD,
        "max": MAX_START_REQUEST_PSRD_THRESHOLD,
    },
    "stop_request_psrd_threshold": {
        "type": "integer",
        "default": DEFAULT_STOP_REQUEST_PSRD_THRESHOLD,
        "min": MIN_STOP_REQUEST_PSRD_THRESHOLD,
        "max": MAX_STOP_REQUEST_PSRD_THRESHOLD,
    },
    "get_psrd_block_size": {
        "type": "integer",
        "default": DEFAULT_GET_PSRD_BLOCK_SIZE,
        "min": MIN_GET_PSRD_BLOCK_SIZE,
        "max": MAX_GET_PSRD_BLOCK_SIZE,
    },
    "min_nr_shares": {
        "type": "integer",
        "default": DEFAULT_MIN_NR_SHARES,
        "min": MIN_MIN_NR_SHARES,
        "max": MAX_MIN_NR_SHARES,
    },
    "hubs": {
        "type": "list",
        "schema": HUB_SCHEMA,
        "default": [],
    },
    "clients": {
        "type": "list",
        "schema": CLIENT_SCHEMA,
        "default": [],
    },
}


def parse_configuration_file(filename: str) -> Configuration:
    """
    Parse the configuration file.
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            try:
                parsed_config = yaml.safe_load(file)
            except yaml.YAMLError as err:
                fatal_error(
                    f"Could not parse configuration file {filename}: {str(err)}"
                )
    except (OSError, IOError) as err:
        fatal_error(f"Could not open configuration file {filename}: {err}")
    validator = cerberus.Validator()
    if not validator.validate(parsed_config, SCHEMA):
        print(f"Could not validate configuration file {filename}", file=sys.stderr)
        pretty_printer = pprint.PrettyPrinter(stream=sys.stderr)
        pretty_printer.pprint(validator.errors)
        sys.exit(1)
    parsed_config = validator.normalized(parsed_config)
    nodes = []
    for parsed_hub_config in parsed_config["hubs"]:
        node_name = parsed_hub_config["name"]
        encryptors = []
        node = Node(NodeType.HUB, node_name, encryptors)
        nodes.append(node)
    for parsed_client_config in parsed_config["clients"]:
        node_name = parsed_client_config["name"]
        parsed_encryptors_config = parsed_client_config["encryptors"]
        if parsed_client_config is None:
            encryptor_names = []
        else:
            encryptor_names = [pec["name"] for pec in parsed_encryptors_config]
        node = Node(NodeType.CLIENT, node_name, encryptor_names)
        nodes.append(node)
    return Configuration(
        parsed_config["base_port"],
        parsed_config["start_request_psrd_threshold"],
        parsed_config["stop_request_psrd_threshold"],
        parsed_config["get_psrd_block_size"],
        parsed_config["min_nr_shares"],
        nodes,
    )
