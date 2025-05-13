#!/usr/bin/env python3

"""
Main entry point for the topology package.
"""

import argparse
import errno
import json
import pprint
import socket
import subprocess
import sys

import cerberus
import requests
import yaml

from common import common


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
                if self.is_topology_already_started():
                    return
                self.start_topology()
            case "stop":
                self.stop_topology()
            case "status":
                self.status_topology()
            case "etsi-qkd":
                self.etsi_qkd()

    def parse_command_line_arguments(self):
        """
        Parse command line arguments.
        """
        parser = argparse.ArgumentParser(description="DSKE Manager")
        parser.add_argument("configfile", help="Configuration filename")
        client_xor_hub_group = parser.add_mutually_exclusive_group()
        client_xor_hub_group.add_argument("--client", help="Filter on client name")
        client_xor_hub_group.add_argument("--hub", help="Filter on hub name")
        subparsers = parser.add_subparsers(dest="command")
        subparsers.required = True
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
        etsi_qkd_parser = subparsers.add_parser(
            "etsi-qkd",
            help="ETSI QKD operations",
        )
        etsi_qkd_parser.add_argument("master_sae_id", help="Master SAE ID")
        etsi_qkd_parser.add_argument("slave_sae_id", help="Slave SAE ID")
        etsi_qkd_subparsers = etsi_qkd_parser.add_subparsers(dest="etsi_qkd_command")
        etsi_qkd_subparsers.required = True
        _etsi_status_parser = etsi_qkd_subparsers.add_parser(
            "status",
            help="Invoke ETSI QKD Status API",
        )
        _etsi_get_key_parser = etsi_qkd_subparsers.add_parser(
            "get-key",
            help="Invoke ETSI QKD Get Key API",
        )
        etsi_get_key_with_id_parser = etsi_qkd_subparsers.add_parser(
            "get-key-with-key-ids",
            help="Invoke ETSI QKD Get Key with Key IDs API",
        )
        etsi_get_key_with_id_parser.add_argument("key_id", help="Key ID")
        _etsi_get_key_pair_parser = etsi_qkd_subparsers.add_parser(
            "get-key-pair",
            help="Invoke ETSI QKD Get Key and Get Key with Key IDs APIs",
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

    def node_url(self, node_type: str, node_name: str) -> str:
        """
        The HTTP base URL for a given node.
        """
        port = self.node_port(node_type, node_name)
        # TODO: Perhaps include the node name as well, so that they can all be hosted on the same
        #       server, which something like Nginx routing requests to the appropriate process.
        return f"http://localhost:{port}"

    def etsi_url(self, node_type: str, node_name: str) -> str:
        """
        The HTTP URL for the ETSI QKD API for a given node.
        """
        return (
            f"{self.node_url(node_type, node_name)}/dske/{node_type}/etsi/api/v1/keys"
        )

    def is_node_filtered(self, node_type: str, node_name: str) -> bool:
        """
        Determine if a node should be filtered out.
        """
        if self._args.client is not None:
            match node_type:
                case "client":
                    return node_name != self._args.client
                case "hub":
                    return True
        if self._args.hub is not None:
            match node_type:
                case "client":
                    return True
                case "hub":
                    return node_name != self._args.hub
        return False

    def is_topology_already_started(self):
        """
        Check if any of the hubs or clients have already been started using two mechanisms:
        1. Does a PID file exist, and if so, does a process with that PID exist?
        2. Is the port already in use?
        """
        some_node_already_started = False
        for hub_config in self._config["hubs"]:
            hub_name = hub_config["name"]
            if self.is_node_filtered("hub", hub_name):
                continue
            some_node_already_started |= self.is_node_already_started("hub", hub_name)
        for client_config in self._config["clients"]:
            client_name = client_config["name"]
            if self.is_node_filtered("client", client_name):
                continue
            some_node_already_started |= self.is_node_already_started(
                "client", client_name
            )
        return some_node_already_started

    def is_node_already_started(self, node_type: str, node_name: str) -> bool:
        """
        Check if a node has already been started.
        """
        return self.is_node_already_started_check_using_pid(
            node_type, node_name
        ) or self.is_node_already_started_check_using_port(node_type, node_name)

    def is_node_already_started_check_using_pid(
        self, node_type: str, node_name: str
    ) -> bool:
        """
        Does a PID file for the node exists, and if so, is there a process running with that PID?
        """
        if not common.pid_file_exists(node_type, node_name):
            return False
        # TODO: Check if PID is already running
        return False

    def is_node_already_started_check_using_port(
        self, node_type: str, node_name: str
    ) -> bool:
        """
        Is the TCP port already in use by some process (might not be a DSKE node, but nevertheless
        it means the DSKE node cannot be started on that port)?
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = self.node_port(node_type, node_name)
        try:
            sock.bind(("", port))
        except OSError as error:
            if error.errno == errno.EADDRINUSE:
                print(f"TCP port {port} for {node_type} {node_name} already in use")
                return True
            return False
        sock.close()
        return False

    def start_topology(self):
        """
        Start all hubs and clients.
        """
        client_extra_args = ["--hubs"]
        for hub_config in self._config["hubs"]:
            hub_name = hub_config["name"]
            if self.is_node_filtered("hub", hub_name):
                continue
            self.start_node("hub", hub_name)
            hub_url = self.node_url("hub", hub_name)
            client_extra_args.append(hub_url)
        for client_config in self._config["clients"]:
            client_name = client_config["name"]
            if self.is_node_filtered("client", client_name):
                continue
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
        # TODO: Append to stdout and stderr instead of replacing it (here and elsewhere)
        _process = subprocess.Popen(
            ["python", "-m", f"{node_type}", node_name, "--port", str(port)]
            + extra_args,
            stdout=out_file,
            stderr=out_file,
        )

    def stop_topology(self):
        """
        Stop all hubs and clients.
        """
        # Stop the clients first, so that they can cleanly unregister from the hubs.
        for client_config in self._config["clients"]:
            client_name = client_config["name"]
            if self.is_node_filtered("client", client_name):
                continue
            self.stop_node("client", client_name)
        for hub_config in self._config["hubs"]:
            hub_name = hub_config["name"]
            if self.is_node_filtered("hub", hub_name):
                continue
            self.stop_node("hub", hub_name)

    def stop_node(self, node_type: str, node_name: str):
        """
        Stop a node (hub or client).
        """
        port = self.node_port(node_type, node_name)
        print(f"Stopping {node_type} {node_name} on port {port}")
        url = f"{self.node_url(node_type, node_name)}/dske/{node_type}/mgmt/v1/stop"
        try:
            _response = requests.post(url, timeout=1.0)
        except requests.exceptions.RequestException as exc:
            print(f"Failed to stop {node_type} {node_name}: {exc}")
        # TODO: Check response (error handling)

    def status_topology(self):
        """
        Report status for all hubs and clients.
        """
        for hub_config in self._config["hubs"]:
            hub_name = hub_config["name"]
            if self.is_node_filtered("hub", hub_name):
                continue
            self.status_node("hub", hub_name)
        for client_config in self._config["clients"]:
            client_name = client_config["name"]
            if self.is_node_filtered("client", client_name):
                continue
            self.status_node("client", client_name)

    def status_node(self, node_type: str, node_name: str):
        """
        Report status for a node (common processing for hubs and clients).
        """
        port = self.node_port(node_type, node_name)
        print(f"Status for {node_type} {node_name} on port {port}")
        url = f"{self.node_url(node_type, node_name)}/dske/{node_type}/mgmt/v1/status"
        try:
            response = requests.get(url, timeout=1.0)
        except requests.exceptions.RequestException as exc:
            print(f"Failed get status for {node_type} {node_name}: {exc}")
            return
        # TODO: Check response (error handling)
        print(json.dumps(response.json(), indent=2))

    def etsi_qkd(self):
        """
        ETSI QKD operations.
        """
        match self._args.etsi_qkd_command:
            case "status":
                self.etsi_qkd_status()
            case "get-key":
                self.etsi_qkd_get_key()
            case "get-key-with-key-ids":
                self.etsi_qkd_get_key_with_key_ids()
            case "get-key-pair":
                self.etsi_qkd_get_key_pair()

    def etsi_qkd_status(self):
        """
        Invoke the ETSI QKD Status API.
        """
        master_sae_id = self._args.master_sae_id
        slave_sae_id = self._args.slave_sae_id
        # See remark about ETSI QKD API in file TODO
        master_client_name = master_sae_id
        port = self.node_port("client", master_client_name)
        print(
            f"Invoke ETSI QKD Status API for client {master_client_name} on port {port}"
        )
        print(f"{master_sae_id=} {slave_sae_id=}")
        url = f"{self.etsi_url("client", master_client_name)}/{slave_sae_id}/status"
        try:
            response = requests.get(url, timeout=1.0)
            # TODO: Check response (error handling)
        except requests.exceptions.RequestException as exc:
            print(f"Failed to invoke ETSI QKD Status API: {exc}")
            return
        print(json.dumps(response.json(), indent=2))

    def etsi_qkd_get_key(self):
        """
        Invoke the ETSI QKD Get Key API.
        """
        # TODO: There is common code with the other ETSI API calls
        master_sae_id = self._args.master_sae_id
        slave_sae_id = self._args.slave_sae_id
        # See remark about ETSI QKD API in file TODO
        master_client_name = master_sae_id
        port = self.node_port("client", master_client_name)
        print(
            f"Invoke ETSI QKD Get Key API for client {master_client_name} on port {port}"
        )
        print(f"{master_sae_id=} {slave_sae_id=}")
        url = f"{self.etsi_url("client", master_client_name)}/{slave_sae_id}/enc_keys"
        try:
            response = requests.get(url, timeout=1.0)
            # TODO: Check response (error handling)
        except requests.exceptions.RequestException as exc:
            print(f"Failed to invoke ETSI QKD Get Key API: {exc}")
            return
        print(json.dumps(response.json(), indent=2))

    def etsi_qkd_get_key_with_key_ids(self):
        """
        Invoke the ETSI QKD Get Key with Key IDs API.
        """
        # TODO: There is common code with the other ETSI API calls
        master_sae_id = self._args.master_sae_id
        slave_sae_id = self._args.slave_sae_id
        # See remark about ETSI QKD API in file TODO
        master_client_name = master_sae_id
        slave_client_name = slave_sae_id
        port = self.node_port("client", master_client_name)
        print(
            f"Invoke ETSI QKD Get Key with Key IDs API for client {slave_client_name} "
            f"on port {port}"
        )
        key_id = self._args.key_id
        print(f"{slave_client_name=} {master_sae_id=} {key_id}")
        url = (
            f"{self.etsi_url("client", slave_client_name)}/{master_sae_id}/dec_keys"
            f"?key_ID={key_id}"
        )
        try:
            response = requests.get(url, timeout=1.0)
            # TODO: Check response (error handling)
        except requests.exceptions.RequestException as exc:
            print(f"Failed to invoke ETSI QKD Get Key API: {exc}")
            return
        print(json.dumps(response.json(), indent=2))

    def etsi_qkd_get_key_pair(self):
        """
        Invoke the ETSI QKD Get Key API on master, followed by Get Key with Key IDs API on slave.
        """
        # TODO: Don't crash if non-existent client name is given
        # TODO: There is common code with the other ETSI API calls
        master_sae_id = self._args.master_sae_id
        slave_sae_id = self._args.slave_sae_id
        # See remark about ETSI QKD API in file TODO
        master_client_name = master_sae_id
        slave_client_name = slave_sae_id
        master_port = self.node_port("client", master_client_name)
        slave_port = self.node_port("client", slave_client_name)
        print(
            f"Invoke ETSI QKD Get Key API for client {master_client_name} on port {master_port}"
        )
        print(f"{master_sae_id=} {slave_sae_id=}")
        url = f"{self.etsi_url("client", master_client_name)}/{slave_sae_id}/enc_keys"
        try:
            get_key_response = requests.get(url, timeout=1.0)
            # TODO: Check response (error handling)
        except requests.exceptions.RequestException as exc:
            print(f"Failed to invoke ETSI QKD Get Key API: {exc}")
            return
        print(json.dumps(get_key_response.json(), indent=2))
        print(
            f"Invoke ETSI QKD Get Key with Key IDs API for client {slave_client_name} "
            f"on port {slave_port}"
        )
        key_id = get_key_response.json()["keys"]["key_ID"]
        key_value_1 = get_key_response.json()["keys"]["key"]
        print(f"{master_sae_id=} {slave_sae_id=} {key_id}")
        url = (
            f"{self.etsi_url("client", slave_client_name)}/{master_sae_id}/dec_keys"
            f"?key_ID={key_id}"
        )
        try:
            get_key_with_key_ids_response = requests.get(url, timeout=1.0)
            # TODO: Check response (error handling)
        except requests.exceptions.RequestException as exc:
            print(f"Failed to invoke ETSI QKD Get Key API: {exc}")
            return
        print(json.dumps(get_key_with_key_ids_response.json(), indent=2))
        key_value_2 = get_key_with_key_ids_response.json()["keys"][0]["key"]
        if key_value_1 == key_value_2:
            print("Key values match")
        else:
            print("Key values do not match")


if __name__ == "__main__":
    manager = Manager()
    manager.main()
