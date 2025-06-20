#!/usr/bin/env python3

"""
Main entry point for the topology package.
"""

import argparse
import errno
import json
import os
import socket
import subprocess
import time

import requests

from common import configuration


class Manager:
    """
    DSKE manager.
    """

    _args: argparse.Namespace
    _nodes: list[(str, str)]  # (node_type, node_name)
    _port_assignments: dict[(str, str), int]  # (node_type, node_name) -> port_nr

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
        match self._args.command:
            case "start":
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
        config = configuration.parse_configuration_file(self._args.configfile)
        self._nodes = config.nodes
        self._port_assignments = config.port_assignments

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
        return f"http://127.0.0.1:{port}"

    def etsi_url(self, node_type: str, node_name: str) -> str:
        """
        The HTTP URL for the ETSI QKD API for a given node.
        """
        return (
            f"{self.node_url(node_type, node_name)}/dske/{node_type}/etsi/api/v1/keys"
        )

    def filtered_nodes(self, reverse_order=False) -> list[(str, str)]:
        """
        Return a list of all nodes in the topology (except those that are filtered), where each node
        is a (node_type, node_name) tuple. Hubs are listed before clients in normal order.
        """
        filtered_nodes = []
        for node_type, node_name in self._nodes:
            if not self.is_node_filtered(node_type, node_name):
                filtered_nodes.append((node_type, node_name))
        if reverse_order:
            filtered_nodes.reverse()
        return filtered_nodes

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

    def is_node_started(self, node_type: str, node_name: str) -> bool:
        """
        Check if a node has been started and is ready to accept API calls.
        """
        return self.is_node_port_in_use(node_type, node_name)

    def is_node_stopped(self, node_type: str, node_name: str) -> bool:
        """
        Check if a node has been stopped and is ready to be restarted.
        """
        return not self.is_node_port_in_use(node_type, node_name)

    def is_node_port_in_use(self, node_type: str, node_name: str) -> bool:
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
                return True
            print(error.errno)
            return False
        sock.close()
        return False

    def start_topology(self):
        """
        Start all hubs and clients.
        """
        if not self.wait_for_all_nodes_stopped():
            print(
                "Not starting topology since nodes from previous topology run were not stopped"
            )
            return
        client_extra_args = ["--hubs"]
        # This code relies on the fact that function nodes() returns hubs before clients
        for node_type, node_name in self.filtered_nodes():
            if node_type == "hub":
                self.start_node(node_type, node_name)
                hub_url = self.node_url("hub", node_name)
                client_extra_args.append(hub_url)
            else:
                self.start_node(node_type, node_name, client_extra_args)
        self.wait_for_all_nodes_started()

    def start_node(
        self, node_type: str, node_name: str, extra_args: list | None = None
    ):
        """
        Start a node (hub or client).
        """
        port = self.node_port(node_type, node_name)
        print(f"Starting {node_type} {node_name} on port {port}")
        out_filename = f"{node_type}-{node_name}.out"
        # TODO: Should we be using a context manager here?
        # pylint: disable=consider-using-with
        out_file = open(out_filename, "w", encoding="utf-8")
        # TODO: Error handling (e.g., if the process fails to start)
        # TODO: Append to stdout and stderr instead of replacing it (here and elsewhere)
        if os.getenv("DSKE_COVERAGE"):
            command = ["python", "-m", "coverage", "run", "-m"]
        else:
            command = ["python", "-m"]
        command += [f"{node_type}", node_name, "--port", str(port)]
        if extra_args is not None:
            command += extra_args
        _process = subprocess.Popen(command, stdout=out_file, stderr=out_file)

    def stop_topology(self):
        """
        Stop all hubs and clients.
        """
        # Stop the clients first, so that they can cleanly unregister from the hubs.
        for node_type, node_name in self.filtered_nodes(reverse_order=True):
            self.stop_node(node_type, node_name)
        self.wait_for_all_nodes_stopped()

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

    def wait_for_all_nodes_condition(self, condition_func, condition_description: str):
        """
        Wait for some condition to be true for all nodes (or give up if it takes too long)
        """
        # TODO: Function type in signature
        print(f"Waiting for all nodes to be {condition_description}")
        max_attempts = 25
        seconds_between_attempts = 3.0
        total_time = max_attempts * seconds_between_attempts
        assert total_time > 60
        first_check = True
        for _ in range(max_attempts):
            all_nodes_meet_condition = True
            for node_type, node_name in self.filtered_nodes():
                if not condition_func(node_type, node_name):
                    all_nodes_meet_condition = False
                    if not first_check:
                        print(
                            f"Still waiting for {node_type} {node_name} "
                            f"to be {condition_description}"
                        )
            if all_nodes_meet_condition:
                return True
            time.sleep(seconds_between_attempts)
            first_check = False
        print(
            f"Giving up on waiting for all nodes to be {condition_description} "
            f"after waiting for {total_time} seconds"
        )
        return False

    def wait_for_all_nodes_started(self):
        """
        Wait for all nodes to be started (or fail if it takes too long)
        """
        return self.wait_for_all_nodes_condition(self.is_node_started, "started")

    def wait_for_all_nodes_stopped(self):
        """
        Wait for all nodes to be stopped (or fail if it takes too long)
        """
        return self.wait_for_all_nodes_condition(self.is_node_stopped, "stopped")

    def status_topology(self):
        """
        Report status for all hubs and clients.
        """
        for node_type, node_name in self.filtered_nodes():
            self.status_node(node_type, node_name)

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
