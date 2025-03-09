"""
Main entry point for the topology package.
"""

import argparse
import json
import pprint
import subprocess
import sys

import cerberus
import requests
import yaml


class Manager:
    """
    DSKE manager.
    """

    _BASE_PORT = 8000

    _args: argparse.Namespace
    _config: dict
    _port_assignments: dict[(str, str), int]  # (node_type, node_name) -> port

    def __init__(self):
        self._args = None
        self._config = None
        self._port_assignments = {}

    def main(self):
        """
        Main entry point for the manager.
        """
        self.parse_command_line_arguments()
        self.parse_configuration()
        self.assign_ports()
        match self._args.command:
            case "start":
                self.start()
            case "stop":
                self.stop()
            case "status":
                self.status()

    def parse_command_line_arguments(self):
        """
        Parse command line arguments.
        """
        parser = argparse.ArgumentParser(description="DSKE Topology")
        parser.add_argument("configfile", help="Configuration filename")
        subparsers = parser.add_subparsers(dest="command")
        _start_parser = subparsers.add_parser(
            "start",
            help="Start all hubs and clients",
        )
        _stop_parser = subparsers.add_parser(
            "stop",
            help="Stop all hubs and clients",
        )
        _status_parser = subparsers.add_parser(
            "status",
            help="Report status for all hubs and clients",
        )
        self._args = parser.parse_args()

    def parse_configuration(self):
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
        filename = self._args.configfile
        try:
            with open(filename, "r", encoding="utf-8") as file:
                try:
                    config = yaml.safe_load(file)
                except yaml.YAMLError as err:
                    print(
                        f"Could not load configuration file {filename}: {str(err)}",
                        file=sys.stderr,
                    )
                    sys.exit(1)
        except (OSError, IOError) as err:
            print(
                f"Could not open configuration file {filename} ({err})", file=sys.stderr
            )
            sys.exit(1)
        validator = cerberus.Validator()
        if not validator.validate(config, schema):
            print(f"Could not parse configuration file {filename}", file=sys.stderr)
            pretty_printer = pprint.PrettyPrinter()
            pretty_printer.pprint(validator.errors)
            sys.exit(1)
        config = validator.normalized(config)
        self._config = config

    def assign_ports(self):
        """
        Assign port numbers to the nodes.
        """
        port = self._BASE_PORT
        for hub_config in self._config["hubs"]:
            self._port_assignments[("hub", hub_config["name"])] = port
            port += 1
        for client_config in self._config["clients"]:
            self._port_assignments[("client", client_config["name"])] = port
            port += 1

    def node_port(self, node_type: str, node_name: str) -> int:
        """
        Determine the port number for a given node.
        """
        return self._port_assignments[(node_type, node_name)]

    def node_url(self, node_type: str, node_name: str) -> int:
        """
        Determine the HTTP URL number for a given node.
        """
        port = self.node_port(node_type, node_name)
        # TODO: Perhaps include the node name as well, so that they can all be hosted on the same
        #       server, which something like Nginx routing requests to the appropriate process.
        return f"http://localhost:{port}/dske/{node_type}"

    def start(self):
        """
        Start all hubs and clients.
        """
        client_extra_args = ["--hubs"]
        for hub_config in self._config["hubs"]:
            hub_name = hub_config["name"]
            self.start_node("hub", hub_name)
            hub_url = self.node_url("hub", hub_name)
            client_extra_args.append(hub_url)
        for client_config in self._config["clients"]:
            client_name = client_config["name"]
            self.start_node("client", client_name, client_extra_args)

    def start_node(
        self, node_type: str, node_name: str, extra_args: list | None = None
    ):
        """
        Start a node (hub or client).
        """
        port = self.node_port(node_type, node_name)
        print(f"Starting {node_type} {node_name} on port {port}")
        if extra_args is None:
            extra_args = []
        out_filename = f"{node_type}-{node_name}.out"
        # TODO: Should we be using a context manager here?
        # pylint: disable=consider-using-with
        out_file = open(out_filename, "w", encoding="utf-8")
        # TODO: Error handling (e.g., if the process fails to start)
        _process = subprocess.Popen(
            ["python", "-m", f"{node_type}", node_name, "--port", str(port)]
            + extra_args,
            stdout=out_file,
            stderr=out_file,
        )

    def stop(self):
        """
        Stop all hubs and clients.
        """
        # Stop the clients first, so that they can cleanly unregister from the hubs.
        for client_config in self._config["clients"]:
            client_name = client_config["name"]
            self.stop_node("client", client_name)
        for hub_config in self._config["hubs"]:
            hub_name = hub_config["name"]
            self.stop_node("hub", hub_name)

    def stop_node(self, node_type: str, node_name: str):
        """
        Stop a node (hub or client).
        """
        port = self.node_port(node_type, node_name)
        print(f"Stopping {node_type} {node_name} on port {port}")
        url = f"{self.node_url(node_type, node_name)}/mgmt/v1/stop"
        try:
            _response = requests.post(url, timeout=1.0)
        except requests.exceptions.RequestException as exc:
            print(f"Failed to stop {node_type} {node_name}: {exc}")
        # TODO: Check response (error handling)

    def status(self):
        """
        Report status for all hubs and clients.
        """
        for hub_config in self._config["hubs"]:
            hub_name = hub_config["name"]
            self.status_node("hub", hub_name)
        for client_config in self._config["clients"]:
            client_name = client_config["name"]
            self.status_node("client", client_name)

    def status_node(self, node_type: str, node_name: str):
        """
        Report status for a node (common processing for hubs and clients).
        """
        port = self.node_port(node_type, node_name)
        print(f"Status for {node_type} {node_name} on port {port}")
        url = f"{self.node_url(node_type, node_name)}/mgmt/v1/status"
        try:
            response = requests.get(url, timeout=1.0)
        except requests.exceptions.RequestException as exc:
            print(f"Failed get status for {node_type} {node_name}: {exc}")
        # TODO: Check response (error handling)
        print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    manager = Manager()
    manager.main()
