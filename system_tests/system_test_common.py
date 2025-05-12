"""
Common functions for the system tests.
"""

import json
import os
import subprocess
import time


_DEFAULT_TOPOLOGY = "topology.yaml"
_DEFAULT_TOPOLOGY_CLIENTS = ["carol", "celia", "cindy", "connie", "curtis"]
# TODO: Is it hilary or hillary?
_DEFAULT_TOPOLOGY_HUBS = ["hank", "helen", "hillary", "holly", "hugo"]
_NODE_START_DELAY = 0.5
_NODE_STOP_DELAY = 0.5
_INITIAL_NODE_PORT = 8000


def start_topology(topology=_DEFAULT_TOPOLOGY):
    """
    Start a topology.
    """
    args = [topology, "start"]
    output = _run_manager(args)
    expected_output = ""
    for hub in _DEFAULT_TOPOLOGY_HUBS:
        expected_output += f"Starting hub {hub} on port {_hub_port(hub)}\n"
    for client in _DEFAULT_TOPOLOGY_CLIENTS:
        expected_output += f"Starting client {client} on port {_client_port(client)}\n"
    assert output == expected_output
    time.sleep(_NODE_START_DELAY)


def stop_topology(topology=_DEFAULT_TOPOLOGY):
    """
    Stop a topology.
    """
    args = [topology, "stop"]
    output = _run_manager(args)
    expected_output = ""
    for client in _DEFAULT_TOPOLOGY_CLIENTS:
        expected_output += f"Stopping client {client} on port {_client_port(client)}\n"
    for hub in _DEFAULT_TOPOLOGY_HUBS:
        expected_output += f"Stopping hub {hub} on port {_hub_port(hub)}\n"
    assert output == expected_output
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
    port = _INITIAL_NODE_PORT
    port += _DEFAULT_TOPOLOGY_HUBS.index(hub)
    return port


def _client_port(client):
    port = _INITIAL_NODE_PORT
    port += len(_DEFAULT_TOPOLOGY_HUBS)
    port += _DEFAULT_TOPOLOGY_CLIENTS.index(client)
    return port


def _run_manager(args):
    """
    Run the manager.
    """
    # TODO: Better method for choosing the directory where manager.py lives
    os.chdir("/Users/brunorijsman/git-personal/dske-python")
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
