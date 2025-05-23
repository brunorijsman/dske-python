"""
Common functions for the system tests.
"""

import json
import os
import re
import subprocess
import time
from common import utils

_DEFAULT_TOPOLOGY = "topology.yaml"
_DEFAULT_TOPOLOGY_CLIENTS = ["carol", "celia", "cindy", "connie", "curtis"]
_DEFAULT_TOPOLOGY_HUBS = ["hank", "helen", "hilary", "holly", "hugo"]
# During coverage testing the delays need to be longer
if os.getenv("DSKE_COVERAGE"):
    _NODE_START_DELAY = 10.0
    _NODE_STOP_DELAY = 60.0
else:
    _NODE_START_DELAY = 5.0
    _NODE_STOP_DELAY = 5.0


def start_topology(topology=_DEFAULT_TOPOLOGY, already_started=False):
    """
    Start a topology.
    """
    args = [topology, "start"]
    output = _run_manager(args)
    expected_output = ""
    for hub in _DEFAULT_TOPOLOGY_HUBS:
        port = _hub_port(hub)
        if already_started:
            expected_output += f"TCP port {port} for hub {hub} in use\n"
        else:
            expected_output += f"Starting hub {hub} on port {port}\n"
    for client in _DEFAULT_TOPOLOGY_CLIENTS:
        port = _client_port(client)
        if already_started:
            expected_output += f"TCP port {port} for client {client} in use\n"
        else:
            expected_output += f"Starting client {client} on port {port}\n"
    assert output == expected_output
    time.sleep(_NODE_START_DELAY)


def stop_topology(topology=_DEFAULT_TOPOLOGY, not_started=False):
    """
    Stop a topology.
    """
    args = [topology, "stop"]
    output = _run_manager(args)
    output_lines = output.split("\n")
    for client in _DEFAULT_TOPOLOGY_CLIENTS:
        assert len(output_lines) > 0
        output_line = output_lines[0]
        output_lines = output_lines[1:]
        port = _client_port(client)
        expected_output = rf"Stopping client {client} on port {port}"
        assert re.search(expected_output, output_line)
        if not_started:
            assert len(output_lines) > 0
            output_line = output_lines[0]
            output_lines = output_lines[1:]
            expected_output = rf"Failed to stop client {client}.*"
            assert re.search(expected_output, output_line)
    for hub in _DEFAULT_TOPOLOGY_HUBS:
        assert len(output_lines) > 0
        output_line = output_lines[0]
        output_lines = output_lines[1:]
        port = _hub_port(hub)
        expected_output = rf"Stopping hub {hub} on port {port}"
        assert re.search(expected_output, output_line)
        if not_started:
            assert len(output_lines) > 0
            output_line = output_lines[0]
            output_lines = output_lines[1:]
            expected_output = rf"Failed to stop hub {hub}.*"
            assert re.search(expected_output, output_line)
    time.sleep(_NODE_STOP_DELAY)


def status_topology(topology=_DEFAULT_TOPOLOGY):
    """
    Get status for a topology.
    """
    status = {}
    status["clients"] = {}
    for client in _DEFAULT_TOPOLOGY_CLIENTS:
        status["clients"][client] = status_node(topology, "client", client)
    status["hubs"] = {}
    for hub in _DEFAULT_TOPOLOGY_HUBS:
        status["hubs"][hub] = status_node(topology, "hub", hub)
    return status


def status_node(topology, node_type, node_name):
    """
    Get status for a client.
    """
    args = [topology, f"--{node_type}", node_name, "status"]
    output = _run_manager(args)
    # Remove header line "Status for {node_type} {node_name} on port {port_nr}"
    output = output.split("\n")
    output = output[1:]
    output = "\n".join(output)
    status = json.loads(output)
    return status


def _hub_port(hub):
    port = utils.TOPOLOGY_BASE_PORT
    port += _DEFAULT_TOPOLOGY_HUBS.index(hub)
    return port


def _client_port(client):
    port = utils.TOPOLOGY_BASE_PORT
    port += len(_DEFAULT_TOPOLOGY_HUBS)
    port += _DEFAULT_TOPOLOGY_CLIENTS.index(client)
    return port


def get_key_pair(master_client: str, slave_client: str) -> None:
    """
    Get a key pair from a pair of DSKE clients using the ETSI QKD API.
    """
    topology = _DEFAULT_TOPOLOGY
    args = [topology, "etsi-qkd", master_client, slave_client, "get-key-pair"]
    output = _run_manager(args)
    expected_output = r".*Key values match"
    assert re.search(expected_output, output)


def _run_manager(args):
    """
    Run the manager.
    """
    root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    os.chdir(root_dir)
    result = subprocess.run(
        ["python", "manager.py"] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0
    assert result.stderr == b""
    output = result.stdout.decode(encoding="utf-8")
    return output
