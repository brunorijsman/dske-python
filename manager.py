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
import httpx
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
        parser.add_argument("--client", help="Filter on client name", action="append")
        parser.add_argument("--hub", help="Filter on hub name", action="append")
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
            "get-status",
            help="Invoke ETSI QKD Get status API",
        )
        etsi_get_key_parser = etsi_qkd_subparsers.add_parser(
            "get-key",
            help="Invoke ETSI QKD Get Key API",
        )
        etsi_get_key_parser.add_argument("--size", help="Key size in bits", type=int)
        etsi_get_key_with_id_parser = etsi_qkd_subparsers.add_parser(
            "get-key-with-key-ids",
            help="Invoke ETSI QKD Get Key with Key IDs API",
        )
        etsi_get_key_with_id_parser.add_argument("key_id", help="Key ID")
        etsi_get_key_pair_parser = etsi_qkd_subparsers.add_parser(
            "get-key-pair",
            help="Invoke ETSI QKD Get Key and Get Key with Key IDs APIs",
        )
        etsi_get_key_pair_parser.add_argument(
            "--size", help="Key size in bits", type=int
        )
        self._args = parser.parse_args()

    def parse_configuration(self):
        """
        Parse the configuration file.
        """
        config = configuration.parse_configuration_file(self._args.configfile)
        self._nodes = config.nodes

    def selected_nodes(self, reverse_order=False) -> list[Node]:
        """
        Return a list of all nodes in the topology (except those that are filtered).
        """
        selected_nodes = []
        for node in self._nodes:
            if self.is_node_selected(node):
                selected_nodes.append(node)
        if reverse_order:
            selected_nodes.reverse()
        return selected_nodes

    def is_node_selected(self, node: Node) -> bool:
        """
        Determine if a node is selected (i.e., not filtered out).
        """
        if self._args.client is None and self._args.hub is None:
            return True
        match node.type:
            case NodeType.CLIENT:
                if self._args.client is None:
                    return False
                return node.name in self._args.client
            case NodeType.HUB:
                if self._args.hub is None:
                    return False
                return node.name in self._args.hub
        assert False, "Unreachable"

    def start_topology(self):
        """
        Start all nodes.
        """
        if not self.wait_for_selected_nodes_stopped():
            print(
                "Not starting topology since nodes from previous topology run were not stopped"
            )
            return
        client_extra_args = []
        for node in self.selected_nodes():
            if node.type == NodeType.HUB:
                client_extra_args.append(node.base_url)
        if client_extra_args:
            client_extra_args = ["--hubs"] + client_extra_args
        # This code relies on the fact that nodes are ordered to have hubs before clients, so that
        # client_extra_args is built up before the first client is started.
        for node in self.selected_nodes():
            if node.type == NodeType.HUB:
                self.start_node(node)
            else:
                self.start_node(node, client_extra_args)
        self.wait_for_selected_nodes_started()

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
        for node in self.selected_nodes(reverse_order=True):
            self.stop_node(node)
        self.wait_for_selected_nodes_stopped()

    def stop_node(self, node: Node):
        """
        Stop a node.
        """
        print(f"Stopping {node.type} {node.name} on port {node.port}")
        url = f"{node.base_url}/mgmt/v1/stop"
        self.http_request(
            "POST", url, f"stop {node.type} {node.name}", quiet_success=True
        )

    def selected_nodes_description(self):
        """
        A human-readable description of the nodes selected by the filtering conditions.
        """
        if self._args.client is None and self._args.hub is None:
            return "all nodes"
        description = ""
        if self._args.client is not None:
            for client_name in self._args.client:
                if description != "":
                    description += ", "
                description += f"client {client_name}"
        if self._args.hub is not None:
            for hub_name in self._args.hub:
                if description != "":
                    description += ", "
                description += f"hub {hub_name}"
        return description

    def wait_for_selected_nodes_condition(
        self, condition_func: typing.Callable[[Node], bool], condition_description: str
    ):
        """
        Wait for some condition to be true for all nodes (or give up if it takes too long)
        """
        which_nodes = self.selected_nodes_description()
        print(f"Waiting for {which_nodes} to be {condition_description}")
        max_attempts = 25
        seconds_between_attempts = 3.0
        total_time = max_attempts * seconds_between_attempts
        assert total_time > 60
        first_check = True
        for _ in range(max_attempts):
            selected_nodes_meet_condition = True
            for node in self.selected_nodes():
                if not condition_func(node):
                    selected_nodes_meet_condition = False
                    if not first_check:
                        print(
                            f"Still waiting for {node.type} {node.name} "
                            f"to be {condition_description}"
                        )
            if selected_nodes_meet_condition:
                return True
            time.sleep(seconds_between_attempts)
            first_check = False
        print(
            f"Giving up on waiting for {which_nodes} to be {condition_description} "
            f"after waiting for {total_time} seconds"
        )
        return False

    def wait_for_selected_nodes_started(self):
        """
        Wait for all nodes to be started (or fail if it takes too long)
        """
        return self.wait_for_selected_nodes_condition(
            lambda node: node.is_started(), "started"
        )

    def wait_for_selected_nodes_stopped(self):
        """
        Wait for all nodes to be stopped (or fail if it takes too long)
        """
        return self.wait_for_selected_nodes_condition(
            lambda node: node.is_stopped(), "stopped"
        )

    def status_topology(self):
        """
        Report status for all hubs and clients.
        """
        for node in self.selected_nodes():
            self.status_node(node)

    def status_node(self, node: Node):
        """
        Report status for a node.
        """
        print(f"Status for {node.type} {node.name} on port {node.port}")
        url = f"{node.base_url}/mgmt/v1/status"
        self.http_request("GET", url, "Management get status")

    def etsi_qkd(self):
        """
        ETSI QKD operations.
        """
        master_node = self.find_kme_node_for_sae(self._args.master_sae_id)
        slave_node = self.find_kme_node_for_sae(self._args.slave_sae_id)
        match self._args.etsi_qkd_command:
            case "get-status":
                self.etsi_qkd_get_status(master_node, slave_node)
            case "get-key":
                size = self._args.size
                self.etsi_qkd_get_key(master_node, slave_node, size)
            case "get-key-with-key-ids":
                key_id = self._args.key_id
                self.etsi_qkd_get_key_with_key_ids(master_node, slave_node, key_id)
            case "get-key-pair":
                size = self._args.size
                self.etsi_qkd_get_key_pair(master_node, slave_node, size)

    def find_kme_node_for_sae(self, sae_id: str) -> Node:
        """
        Given an SAE ID, find the KME node that is associated with it.
        """
        # For now we make the simplifying assumption that there is only one SAE (encryptor) attached
        # to each KME (client), and that the SAE has the same name as the KME. This makes the code
        # simpler, since the KMEs don't need to keep track of which SAEs are attached to them.
        for node in self._nodes:
            if node.type == NodeType.CLIENT and node.name == sae_id:
                return node
        self.fatal_error(f"Could not find KME client node for SAE ID {sae_id}")

    def etsi_qkd_get_status(self, master_node: Node, slave_node: Node):
        """
        Invoke the ETSI QKD Status API.
        """
        print(
            f"Invoke ETSI QKD Status API for client {master_node.name} on port {master_node.port}"
        )
        url = f"{master_node.base_url}/etsi/api/v1/keys/{slave_node.name}/status"
        self.http_request("GET", url, "ETSI QKD Get status")

    def etsi_qkd_get_key(
        self,
        master_node: Node,
        slave_node: Node,
        size: int | None,
    ) -> None | dict:
        """
        Invoke the ETSI QKD Get Key API.
        """
        print(
            f"Invoke ETSI QKD Get Key API for client {master_node.name} on port {master_node.port}"
        )
        url = f"{master_node.base_url}/etsi/api/v1/keys/{slave_node.name}/enc_keys"
        params = {}
        if size is not None:
            params["size"] = size
        response = self.http_request("GET", url, "ETSI QKD Get key", params=params)
        return response

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
        url = f"{slave_node.base_url}/etsi/api/v1/keys/{master_node.name}/dec_keys"
        params = {"key_ID": key_id}
        response = self.http_request(
            "GET", url, "ETSI QKD Get key with key IDs", params=params
        )
        if response is None:
            return None
        return response.json()

    def etsi_qkd_get_key_pair(
        self,
        master_node: Node,
        slave_node: Node,
        size: int | None,
    ):
        """
        Invoke the ETSI QKD Get Key API on master, followed by Get Key with Key IDs API on slave.
        """
        response = self.etsi_qkd_get_key(master_node, slave_node, size)
        if response is None:
            return
        if response.status_code != 200:
            return
        master_response_json = response.json()
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

    def http_request(
        self,
        method: str,
        url: str,
        action: str | None,
        params: dict | None = None,
        quiet_success: bool = False,
    ) -> httpx.Response:
        """
        Make an HTTP request.
        """
        try:
            response = httpx.request(method=method, url=url, params=params, timeout=1.0)
        except httpx.HTTPError as exc:
            if action is not None:
                print(f"Failed to {action}: {method} {url} raised exception {exc}")
            return None
        if response.status_code != 200:
            print(
                f"Failed to {action}: {method} {url} returned status code {response.status_code}"
            )
        if not quiet_success:
            try:
                response_json = response.json()
                print(json.dumps(response_json, indent=2))
            except json.JSONDecodeError:
                print(response.text)
        return response


if __name__ == "__main__":
    manager = Manager()
    manager.main()
