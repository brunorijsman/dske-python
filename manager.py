#!/usr/bin/env python3

"""
Main entry point for the topology package.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import typing
import requests
from common import configuration
from common.node import Node, NodeType


class Manager:
    """
    DSKE manager.
    """

    _args: None | argparse.Namespace
    _nodes: None | list[Node]

    def __init__(self):
        self._args = None
        self._nodes = None

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

    @staticmethod
    def error(message: str):
        """
        Print an error message and continue.
        """
        print(f"Error: {message}", file=sys.stderr)

    @staticmethod
    def fatal_error(message: str) -> typing.NoReturn:
        """
        Print a fatal error message and exit.
        """
        print(f"Fatal error: {message}", file=sys.stderr)
        sys.exit(1)

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

    def filtered_nodes(self, reverse_order=False) -> list[Node]:
        """
        Return a list of all nodes in the topology (except those that are filtered).
        """
        filtered_nodes = []
        for node in self._nodes:
            if not self.is_node_filtered(node):
                filtered_nodes.append(node)
        if reverse_order:
            filtered_nodes.reverse()
        return filtered_nodes

    def is_node_filtered(self, node: Node) -> bool:
        """
        Determine if a node should be filtered out.
        """
        if self._args.client is not None:
            match node.type:
                case NodeType.CLIENT:
                    return node.name != self._args.client
                case NodeType.HUB:
                    return True
        if self._args.hub is not None:
            match node.type:
                case NodeType.CLIENT:
                    return True
                case NodeType.HUB:
                    return node.name != self._args.hub
        return False

    def start_topology(self):
        """
        Start all nodes.
        """
        if not self.wait_for_all_nodes_stopped():
            print(
                "Not starting topology since nodes from previous topology run were not stopped"
            )
            return
        client_extra_args = []
        for node in self.filtered_nodes():
            if node.type == NodeType.HUB:
                client_extra_args.append(node.base_url)
        if client_extra_args:
            client_extra_args = ["--hubs"] + client_extra_args
        # This code relies on the fact that nodes are ordered to have hubs before clients, so that
        # client_extra_args is built up before the first client is started.
        for node in self.filtered_nodes():
            if node.type == NodeType.HUB:
                self.start_node(node)
            else:
                self.start_node(node, client_extra_args)
        self.wait_for_all_nodes_started()

    def start_node(self, node: Node, extra_args: list | None = None):
        """
        Start a node.
        """
        print(f"Starting {node.type} {node.name} on port {node.port}")
        out_filename = f"{node.type}-{node.name}.out"
        # TODO: Should we be using a context manager here?
        # pylint: disable=consider-using-with
        out_file = open(out_filename, "a", encoding="utf-8")
        # TODO: Error handling (e.g., if the process fails to start)
        # TODO: Append to stdout and stderr instead of replacing it (here and elsewhere)
        if os.getenv("DSKE_COVERAGE"):
            command = ["python", "-m", "coverage", "run", "-m"]
        else:
            command = ["python", "-m"]
        command += [f"{node.type}", node.name, "--port", str(node.port)]
        if extra_args is not None:
            command += extra_args
        _process = subprocess.Popen(command, stdout=out_file, stderr=out_file)

    def stop_topology(self):
        """
        Stop all nodes.
        """
        # Stop the clients first, so that they can cleanly unregister from the hubs.
        for node in self.filtered_nodes(reverse_order=True):
            self.stop_node(node)
        self.wait_for_all_nodes_stopped()

    def stop_node(self, node: Node):
        """
        Stop a node.
        """
        print(f"Stopping {node.type} {node.name} on port {node.port}")
        url = f"{node.base_url}/mgmt/v1/stop"
        try:
            _response = requests.post(url, timeout=1.0)
        except requests.exceptions.RequestException as exc:
            print(f"Failed to stop {node.type} {node.name}: {exc}")
        # TODO: Check response (error handling)

    def wait_for_all_nodes_condition(
        self, condition_func: typing.Callable[[Node], bool], condition_description: str
    ):
        """
        Wait for some condition to be true for all nodes (or give up if it takes too long)
        """
        print(f"Waiting for all nodes to be {condition_description}")
        max_attempts = 25
        seconds_between_attempts = 3.0
        total_time = max_attempts * seconds_between_attempts
        assert total_time > 60
        first_check = True
        for _ in range(max_attempts):
            all_nodes_meet_condition = True
            for node in self.filtered_nodes():
                if not condition_func(node):
                    all_nodes_meet_condition = False
                    if not first_check:
                        print(
                            f"Still waiting for {node.type} {node.name} "
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
        return self.wait_for_all_nodes_condition(
            lambda node: node.is_started(), "started"
        )

    def wait_for_all_nodes_stopped(self):
        """
        Wait for all nodes to be stopped (or fail if it takes too long)
        """
        return self.wait_for_all_nodes_condition(
            lambda node: node.is_stopped(), "stopped"
        )

    def status_topology(self):
        """
        Report status for all hubs and clients.
        """
        for node in self.filtered_nodes():
            self.status_node(node)

    def status_node(self, node: Node):
        """
        Report status for a node.
        """
        print(f"Status for {node.type} {node.name} on port {node.port}")
        url = f"{node.base_url}/mgmt/v1/status"
        try:
            response = requests.get(url, timeout=1.0)
        except requests.exceptions.RequestException as exc:
            print(f"Failed get status for {node.type} {node.name}: {exc}")
            return
        # TODO: Check response (error handling)
        print(json.dumps(response.json(), indent=2))

    def etsi_qkd(self):
        """
        ETSI QKD operations.
        """
        master_node = self.find_kme_node_for_sae(self._args.master_sae_id)
        slave_node = self.find_kme_node_for_sae(self._args.slave_sae_id)
        match self._args.etsi_qkd_command:
            case "status":
                self.etsi_qkd_status(master_node, slave_node)
            case "get-key":
                self.etsi_qkd_get_key(master_node, slave_node)
            case "get-key-with-key-ids":
                key_id = self._args.key_id
                self.etsi_qkd_get_key_with_key_ids(master_node, slave_node, key_id)
            case "get-key-pair":
                self.etsi_qkd_get_key_pair(master_node, slave_node)

    def find_kme_node_for_sae(self, sae_id: str) -> Node:
        """
        Given an SAE ID, find the KME node that is associated with it.
        TODO: For now we make the simplifying assumption that there is only one SAE attached
              to each KME, and that the KME has the same name as the KME
        """
        for node in self._nodes:
            if node.type == NodeType.CLIENT and node.name == sae_id:
                return node
        self.fatal_error(f"Could not find KME client node for SAE ID {sae_id}")

    def etsi_qkd_status(self, master_node: Node, slave_node: Node):
        """
        Invoke the ETSI QKD Status API.
        """
        print(
            f"Invoke ETSI QKD Status API for client {master_node.name} on port {master_node.port}"
        )
        url = f"{master_node.base_url}/etsi/api/v1/keys/{slave_node.name}/status"
        try:
            response = requests.get(url, timeout=1.0)
            # TODO: Check response (error handling)
        except requests.exceptions.RequestException as exc:
            self.error(f"Failed to invoke ETSI QKD Status API: {exc}")
            return
        print(json.dumps(response.json(), indent=2))

    def etsi_qkd_get_key(self, master_node: Node, slave_node: Node) -> None | dict:
        """
        Invoke the ETSI QKD Get Key API.
        """
        print(
            f"Invoke ETSI QKD Get Key API for client {master_node.name} on port {master_node.port}"
        )
        url = f"{master_node.base_url}/etsi/api/v1/keys/{slave_node.name}/enc_keys"
        try:
            response = requests.get(url, timeout=1.0)
            # TODO: Check response (error handling)
        except requests.exceptions.RequestException as exc:
            # TODO Better error handling
            self.error(f"Failed to invoke ETSI QKD Get Key API: {exc}")
            return None
        print(json.dumps(response.json(), indent=2))
        return response.json()

    def etsi_qkd_get_key_with_key_ids(
        self, master_node: Node, slave_node: Node, key_id: str
    ) -> dict:
        """
        Invoke the ETSI QKD Get Key with Key IDs API.
        """
        print(
            f"Invoke ETSI QKD Get Key with Key IDs API for client {slave_node.name} "
            f"on port {slave_node.port}"
        )
        url = f"{master_node.base_url}/etsi/api/v1/keys/{slave_node.name}/dec_keys?key_ID={key_id}"
        try:
            response = requests.get(url, timeout=1.0)
            # TODO: Check response (error handling)
        except requests.exceptions.RequestException as exc:
            self.error(f"Failed to invoke ETSI QKD Get Key API: {exc}")
        print(f"{response=}")
        print(f"json={json.dumps(response.json(), indent=2)}")
        return response.json()

    def etsi_qkd_get_key_pair(self, master_node: Node, slave_node: Node):
        """
        Invoke the ETSI QKD Get Key API on master, followed by Get Key with Key IDs API on slave.
        """
        master_response_json = self.etsi_qkd_get_key(master_node, slave_node)
        key_id = master_response_json["keys"]["key_ID"]
        slave_response_json = self.etsi_qkd_get_key_with_key_ids(
            master_node, slave_node, key_id
        )
        master_key_value = master_response_json["keys"]["key"]
        slave_key_value = slave_response_json["keys"][0]["key"]
        if master_key_value == slave_key_value:
            print("Key values match")
        else:
            print("Key values do not match")


if __name__ == "__main__":
    manager = Manager()
    manager.main()
