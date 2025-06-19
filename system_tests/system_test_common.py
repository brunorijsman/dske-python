"""
Common functions for the system tests.
"""

import json
import os
import re
import subprocess
from common import utils

_DEFAULT_TOPOLOGY = "topology.yaml"
_DEFAULT_TOPOLOGY_NODES = [
    ("hub", name) for name in ["hank", "helen", "hilary", "holly", "hugo"]
] + [("client", name) for name in ["carol", "celia", "cindy", "connie", "curtis"]]


def start_topology(topology=_DEFAULT_TOPOLOGY, already_started=False):
    """
    Start a topology.
    """
    args = [topology, "start"]
    output = _run_manager(args)
    expected_output = ""
    for node_type, node_name in _DEFAULT_TOPOLOGY_NODES:
        port = _node_port(node_type, node_name)
        if already_started:
            expected_output += f"TCP port {port} for {node_type} {node_name} in use\n"
        else:
            expected_output += f"Starting {node_type} {node_name} on port {port}\n"
    assert output == expected_output


def stop_topology(topology=_DEFAULT_TOPOLOGY, not_started=False):
    """
    Stop a topology.
    """
    args = [topology, "stop"]
    output = _run_manager(args)
    output_lines = output.split("\n")
    for node_type, node_name in _DEFAULT_TOPOLOGY_NODES.reverse:
        assert len(output_lines) > 0
        output_line = output_lines[0]
        output_lines = output_lines[1:]
        port = _node_port(node_type, node_name)
        expected_output = rf"Stopping {node_type} {node_name} on port {port}"
        assert re.search(expected_output, output_line)
        if not_started:
            assert len(output_lines) > 0
            output_line = output_lines[0]
            output_lines = output_lines[1:]
            expected_output = rf"Failed to stop {node_type} {node_name}.*"
            assert re.search(expected_output, output_line)


def status_topology(topology=_DEFAULT_TOPOLOGY):
    """
    Get status for a topology.
    """
    status = {}
    status["clients"] = {}
    for node_type, node_name in _DEFAULT_TOPOLOGY_NODES:
        status[(node_type, node_name)] = status_node(topology, node_type, node_name)
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


def _node_port(node_type: str, node_name: str) -> int:
    port = utils.TOPOLOGY_BASE_PORT
    port += _DEFAULT_TOPOLOGY_NODES.index((node_type, node_name))
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
