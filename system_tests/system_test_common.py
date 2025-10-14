"""
Common functions for the system tests.
"""

import json
import os
import re
import subprocess
from typing import Tuple
from common import configuration


def start_topology():
    """
    Start a topology.
    """
    args = [configuration.DEFAULT_CONFIGURATION_FILE, "start"]
    output = _run_manager(args)
    check_wait_for_all_nodes_stopped_output(output)
    config = configuration.parse_configuration_file()
    for node in config.nodes:
        expected_line = rf"Starting {node.type} {node.name} on port {node.port}"
        assert next_output_matches(output, expected_line)
    check_wait_for_all_nodes_started_output(output)
    check_no_more_output(output)


def start_topology_again():
    """
    Start a topology again (after it has already been started).
    This is expected to fail: waiting for the nodes from the "previous run" to stop will time out.
    """
    args = [configuration.DEFAULT_CONFIGURATION_FILE, "start"]
    output = _run_manager(args)
    some_output_matches(output, r"Giving up on waiting for all nodes to be stopped")


def stop_topology(
    not_started: bool = False,
    not_started_node: None | Tuple[str, str] = None,
):
    """
    Stop a topology.
    """
    # Initiate shutdown of each node
    args = [configuration.DEFAULT_CONFIGURATION_FILE, "stop"]
    output = _run_manager(args)
    config = configuration.parse_configuration_file()
    for node in reversed(config.nodes):
        line = rf"Stopping {node.type} {node.name} on port {node.port}"
        assert next_output_matches(output, line)
        if not_started:
            expect_failure = True
        elif (
            not_started_node is not None
            and node.type == not_started_node[0]
            and node.name == not_started_node[1]
        ):
            expect_failure = True
        else:
            expect_failure = False
        line = rf"Failed to stop {node.type} {node.name}"
        if expect_failure:
            assert next_output_matches(output, line)
        else:
            assert not next_output_matches(output, line)
    check_wait_for_all_nodes_stopped_output(output)


def stop_node(node_type: str, node_name: str):
    """
    Stop a node.
    """
    args = [
        configuration.DEFAULT_CONFIGURATION_FILE,
        f"--{node_type}",
        node_name,
        "stop",
    ]
    output = _run_manager(args)
    line = rf"Stopping {node_type} {node_name} on port"
    assert next_output_matches(output, line)
    check_wait_for_all_nodes_stopped_output(output)


def next_output_matches(output, expected_line):
    """
    Check that the NEXT line of output from the manager matches an expected string.
    If the line matches, return True and consume the line from the output.
    If the line does not match, return False and do not consume the line from the output.
    """
    assert len(output) > 0
    output_line = output[0]
    if re.search(expected_line, output_line):
        consume_line(output)
        return True
    return False


def some_output_matches(output, expected_line):
    """
    Check that SOME line of output from the manager matches an expected string.
    If the line matches, return True and consume the line from the output.
    If the line does not match, return False and do not consume the line from the output.
    """
    while len(output) > 0:
        if next_output_matches(output, expected_line):
            return True
        consume_line(output)
    return False


def consume_line(output):
    """
    Consume a line of output.
    """
    # Note: output = output[1:] does not work here, because it only changes the local
    # parameter output in this function and not the argument passed in by the caller.
    output.reverse()
    output.pop()
    output.reverse()


def check_no_more_output(output):
    """
    Check that there is no more output.
    """
    # Consume blank lines
    while len(output) > 0 and next_output_matches(output, r" *"):
        pass
    # Do this instead of assert len(output) != 0 to see the offending output in the assert message
    if len(output) != 0:
        assert not output[0]


def check_wait_for_all_nodes_stopped_output(output):
    """
    Check the output of the manager for the part where it waits for all nodes to be stopped.
    """
    assert next_output_matches(output, r"Waiting for all nodes to be stopped")
    while next_output_matches(output, r"Still waiting for .* to be stopped"):
        pass
    assert not next_output_matches(
        output, r"Giving up on waiting for all nodes to be stopped"
    )


def check_wait_for_all_nodes_started_output(output):
    """
    Check the output of the manager for the part where it waits for all nodes to be started.
    """
    assert next_output_matches(output, r"Waiting for all nodes to be started")
    while next_output_matches(output, r"Still waiting for .* to be started"):
        pass
    assert not next_output_matches(
        output, r"Giving up on waiting for all nodes to be started"
    )


def status_topology():
    """
    Get status for a topology.
    """
    status = {}
    status["clients"] = {}
    config = configuration.parse_configuration_file()
    for node in config.nodes:
        status_node(node)


def status_node(node):
    """
    Get status for a client.
    """
    args = [
        configuration.DEFAULT_CONFIGURATION_FILE,
        f"--{node.type}",
        node.name,
        "status",
    ]
    output = _run_manager(args)
    assert next_output_matches(output, r"Status for .* .* on port .*")
    output = "\n".join(output)
    status = json.loads(output)
    return status


def get_key_pair(master_client: str, slave_client: str) -> None:
    """
    Get a key pair from a pair of DSKE clients using the ETSI QKD API.
    """
    args = [
        configuration.DEFAULT_CONFIGURATION_FILE,
        "etsi-qkd",
        master_client,
        slave_client,
        "get-key-pair",
    ]
    output = _run_manager(args)
    assert some_output_matches(output, r"Key values match")


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
    output = result.stdout.decode(encoding="utf-8").split("\n")
    return output
