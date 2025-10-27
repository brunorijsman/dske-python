"""
Common functions for the system tests.
"""

import json
import os
import re
import sys
import subprocess
from typing import List, Tuple
from common import configuration
from common.node import NodeType


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
    stopped_nodes: None | List[Tuple[str, str]] = None,
):
    """
    Stop a topology.
    """
    print(f"{stopped_nodes=}", file=sys.stderr)
    # Initiate shutdown of each node
    args = [configuration.DEFAULT_CONFIGURATION_FILE, "stop"]
    output = _run_manager(args)
    config = configuration.parse_configuration_file()
    for node in reversed(config.nodes):
        line = rf"Stopping {node.type} {node.name} on port {node.port}"
        assert next_output_matches(output, line)
        if not_started:
            expect_failure = True
        elif stopped_nodes is not None:
            expect_failure = False
            for stopped_node_type_str, stopped_node_name in stopped_nodes:
                stopped_node_type = NodeType.from_str(stopped_node_type_str)
                if node.type == stopped_node_type and node.name == stopped_node_name:
                    expect_failure = True
                    break
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
    assert next_output_matches(output, r"Waiting for .* to be stopped")
    while next_output_matches(output, r"Still waiting for .* to be stopped"):
        pass
    assert not next_output_matches(output, r"Giving up on waiting for .* to be stopped")


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
    config = configuration.parse_configuration_file()
    for node in config.nodes:
        node_type = str(node.type)
        node_name = node.name
        status[(node_type, node_name)] = status_node(node_type, node_name)
    return status


def status_node(node_type, node_name):
    """
    Get status for a node.
    """
    args = [
        configuration.DEFAULT_CONFIGURATION_FILE,
        f"--{node_type}",
        node_name,
        "status",
    ]
    output = _run_manager(args)
    assert next_output_matches(output, r"Status for .* .* on port .*")
    output = "\n".join(output)
    status = json.loads(output)
    return status


def check_output(
    output,
    expected_status_code: int,
    expected_output_lines: None | List[str],
):
    """
    Check output from the manager.
    """
    if expected_status_code != 200:
        assert some_output_matches(output, rf"status code {expected_status_code}")
    if expected_output_lines is not None:
        for expected_output_line in expected_output_lines:
            assert some_output_matches(output, expected_output_line)


def extract_key_id(output) -> None | str:
    """
    Extract the key ID from the output of a Get Key request.
    """
    for line in output:
        print(f"Searching for key ID in line: <{line}>", file=sys.stderr)  ### DEBUG
        match = re.search(r'"key_ID": "(\S+)"', line)
        print(f"{match=}", file=sys.stderr)  ### DEBUG
        if match:
            return match.group(1)
    return None


def get_status(
    master_client: str,
    slave_client: str,
    expected_status_code: int = 200,
    expected_output_lines: None | List[str] = None,
) -> None | str:
    """
    Get key from a pair of DSKE clients using the ETSI QKD API.
    Returns the key ID as a string on success or None on failure.
    """
    args = [
        configuration.DEFAULT_CONFIGURATION_FILE,
        "etsi-qkd",
        master_client,
        slave_client,
        "get-status",
    ]
    output = _run_manager(args)
    check_output(output, expected_status_code, expected_output_lines)


def get_key(
    master_client: str,
    slave_client: str,
    expected_status_code: int = 200,
    expected_output_lines: None | List[str] = None,
) -> None | str:
    """
    Get key from a pair of DSKE clients using the ETSI QKD API.
    Returns the key ID as a string on success or None on failure.
    """
    args = [
        configuration.DEFAULT_CONFIGURATION_FILE,
        "etsi-qkd",
        master_client,
        slave_client,
        "get-key",
    ]
    output = _run_manager(args)
    check_output(output, expected_status_code, expected_output_lines)
    if expected_status_code == 200:
        key_id = extract_key_id(output)
        return key_id
    return None


def get_key_with_key_ids(
    master_client: str,
    slave_client: str,
    key_id: str,
    expected_status_code: int = 200,
    expected_output_lines: None | List[str] = None,
) -> None:
    """
    Get key with key IDs from a pair of DSKE clients using the ETSI QKD API.
    """
    args = [
        configuration.DEFAULT_CONFIGURATION_FILE,
        "etsi-qkd",
        master_client,
        slave_client,
        "get-key-with-key-ids",
        key_id,
    ]
    output = _run_manager(args)
    check_output(output, expected_status_code, expected_output_lines)


def get_key_pair(
    master_client: str,
    slave_client: str,
    size: int | None = None,
) -> None:
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
    if size is not None:
        args += ["--size", str(size)]
    output = _run_manager(args)
    check_output(output, 200, [r"Key values match"])


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
    output = result.stdout.decode(encoding="utf-8").split("\n")
    return output
