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
        if node.encryptor_names:
            command += ["--encryptors"] + node.encryptor_names
        if extra_args is not None:
            command += extra_args
        _process = subprocess.Popen(command, stdout=out_file, stderr=out_file)

    def stop_topology(self):
        """
        Stop all nodes.
        """
        # Stop the clients first, in case we implement unregistration at some point
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
        # ETSI QKD 014 uses different terminology than DSKE:
        #
        # ETSI QKD 014 term                   DSKE term
        # ----------------------------------  ----------------------------------
        # SAE (Secure Application Entity)     Encryptor
        # SAE ID                              Encryptor name
        # KME (Key Management Entity)         Client
        # KME ID                              Client name
        # N/A                                 Hub
        # N/A                                 Hub name
        #
        # In the code related to ETSI QKD 014, we use the ETSI terminology.
        #
        master_sae_id = self._args.master_sae_id
        slave_sae_id = self._args.slave_sae_id
        master_kme_node = self.find_kme_node_for_sae_id(master_sae_id)
        slave_kme_node = self.find_kme_node_for_sae_id(slave_sae_id)
        match self._args.etsi_qkd_command:
            case "get-status":
                self.etsi_qkd_get_status(master_kme_node, master_sae_id, slave_sae_id)
            case "get-key":
                size = self._args.size
                self.etsi_qkd_get_key(
                    master_kme_node, master_sae_id, slave_sae_id, size
                )
            case "get-key-with-key-ids":
                key_id = self._args.key_id
                self.etsi_qkd_get_key_with_key_ids(
                    slave_kme_node, master_sae_id, slave_sae_id, key_id
                )
            case "get-key-pair":
                size = self._args.size
                self.etsi_qkd_get_key_pair(
                    master_kme_node, slave_kme_node, master_sae_id, slave_sae_id, size
                )

    def find_kme_node_for_sae_id(self, sae_id: str) -> Node:
        """
        Given an encryptor name (SAE ID), find the client node (KME) that is associated with it.
        """
        for node in self._nodes:
            if node.type == NodeType.CLIENT and sae_id in node.encryptor_names:
                return node
        self.fatal_error(
            f"There is no encryptor (SAE) in the topology with name (SAE ID) {sae_id}"
        )

    # In the following ETSI QKD 014 API calls, the master SAE ID neither passed in a request query
    # parameter nor passed as a JSON attribute in the request body. In real life, the KME would
    # determine the SAE ID from the TLS authentication. However, we only have a simplified
    # implementation of ETSI QKD 014 without HTTPS (TLS). For that reason, we pass the master SAE ID
    # in cleartext in an HTTP "Authorization" header. This is, of course, not secure, but it is
    # sufficient for our simplified implementation and testing purposes.

    def _etsi_qkd_report_call(
        self, api_name: str, kme_node: Node, master_sae_id: str, slave_sae_id: str
    ):
        print(
            f"Invoke ETSI QKD {api_name} API "
            f"on client (KME) {kme_node.name} "
            f"port {kme_node.port} "
            f"master encryptor (SAE) {master_sae_id} "
            f"slave encryptor (SAE) {slave_sae_id}:"
        )

    def etsi_qkd_get_status(
        self,
        master_kme_node: Node,
        master_sae_id: str,
        slave_sae_id: str,
    ):
        """
        Invoke the ETSI QKD Status API.
        """
        self._etsi_qkd_report_call(
            "Status", master_kme_node, master_sae_id, slave_sae_id
        )
        url = f"{master_kme_node.base_url}/etsi/api/v1/keys/{slave_sae_id}/status"
        self.http_request(
            "GET",
            url,
            "ETSI QKD Get status",
            headers={"Authorization": master_sae_id},
        )

    def etsi_qkd_get_key(
        self,
        master_kme_node: Node,
        master_sae_id: str,
        slave_sae_id: str,
        size: int | None,
    ) -> None | dict:
        """
        Invoke the ETSI QKD Get Key API.
        """
        self._etsi_qkd_report_call(
            "Get Key", master_kme_node, master_sae_id, slave_sae_id
        )
        url = f"{master_kme_node.base_url}/etsi/api/v1/keys/{slave_sae_id}/enc_keys"
        params = {}
        if size is not None:
            params["size"] = size
        response = self.http_request(
            "GET",
            url,
            "ETSI QKD Get key",
            params=params,
            headers={"Authorization": master_sae_id},
        )
        return response

    def etsi_qkd_get_key_with_key_ids(
        self,
        slave_kme_node: Node,
        master_sae_id: str,
        slave_sae_id: str,
        key_id: str,
    ) -> None | dict:
        """
        Invoke the ETSI QKD Get Key with Key IDs API.
        """
        self._etsi_qkd_report_call(
            "Get Key with Key IDs", slave_kme_node, master_sae_id, slave_sae_id
        )
        url = f"{slave_kme_node.base_url}/etsi/api/v1/keys/{master_sae_id}/dec_keys"
        params = {"key_ID": key_id}
        response = self.http_request(
            "GET",
            url,
            "ETSI QKD Get key with key IDs",
            params=params,
            headers={"Authorization": slave_sae_id},
        )
        return response

    def etsi_qkd_get_key_pair(
        self,
        master_kme_node: Node,
        slave_kme_node: None,
        master_sae_id: str,
        slave_sae_id: str,
        size: int | None,
    ):
        """
        Invoke the ETSI QKD Get Key API on master, followed by Get Key with Key IDs API on slave.
        """
        master_response = self.etsi_qkd_get_key(
            master_kme_node, master_sae_id, slave_sae_id, size
        )
        if master_response is None:
            return
        if master_response.status_code != 200:
            return
        master_response_json = master_response.json()
        key_id = master_response_json["keys"]["key_ID"]
        master_key_value = master_response_json["keys"]["key"]
        slave_response = self.etsi_qkd_get_key_with_key_ids(
            slave_kme_node, master_sae_id, slave_sae_id, key_id
        )
        if slave_response is None:
            return
        if slave_response.status_code != 200:
            return
        slave_response_json = slave_response.json()
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
        headers: dict | None = None,
        quiet_success: bool = False,
    ) -> httpx.Response:
        """
        Make an HTTP request.
        """
        try:
            response = httpx.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                timeout=1.0,
            )
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
