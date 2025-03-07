"""
Main entry point for the topology package.
"""

import argparse
import json
import subprocess

import requests

from . import config

_BASE_PORT = 8000


def main():
    """
    Main entry point for the topology package.
    """
    args = parse_command_line_arguments()
    parsed_config = config.parse_configuration(args.configfile)
    match args.command:
        case "start":
            start_topology(parsed_config)
        case "stop":
            stop_topology(parsed_config)
        case "status":
            status_topology(parsed_config)


def parse_command_line_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="DSKE Topology")
    parser.add_argument("configfile", help="Configuration filename")
    parser.add_argument("command", choices=["start", "stop", "status"])
    args = parser.parse_args()
    return args


def start_topology(parsed_config: dict):
    """
    Start the topology.
    """
    port = _BASE_PORT
    hub_extra_args = ["--hubs"]
    for hub_config in parsed_config["hubs"]:
        start_hub(hub_config, port)
        hub_extra_args.append(f"http://localhost:{port}")
        port += 1
    for client_config in parsed_config["clients"]:
        start_client(client_config, port, hub_extra_args)
        port += 1


def stop_topology(parsed_config: dict):
    """
    Stop the topology.
    """
    port = _BASE_PORT
    # TODO: Stop the clients first, to make unregistering more orderly. We can't simply swap
    #       the loops because port assignment needs to be deterministic.
    for hub_config in parsed_config["hubs"]:
        stop_hub(hub_config, port)
        port += 1
    for client_config in parsed_config["clients"]:
        stop_client(client_config, port)
        port += 1


def status_topology(parsed_config: dict):
    """
    Report status for the entire topology.
    """
    port = _BASE_PORT
    for hub_config in parsed_config["hubs"]:
        status_hub(hub_config, port)
        port += 1
    for client_config in parsed_config["clients"]:
        status_client(client_config, port)
        port += 1


def start_hub(hub_config: dict, port: int):
    """
    Start a hub.
    """
    name = hub_config["name"]
    print(f"Starting hub {hub_config['name']} on port {port}")
    start_node("hub", name, port)


def start_client(client_config: dict, port: int, hub_extra_args: list):
    """
    Start a client.
    """
    name = client_config["name"]
    print(f"Starting client {name} on port {port}")
    start_node("client", name, port, hub_extra_args)


def start_node(node_type: str, node_name: str, port: int, extra_args=None):
    """
    Start a node (common processing for hubs and clients).
    """
    if extra_args is None:
        extra_args = []
    out_filename = f"{node_type}-{node_name}.out"
    # TODO: Should we be using a context manager here?
    # pylint: disable=consider-using-with
    out_file = open(out_filename, "w", encoding="utf-8")
    # TODO: Error handling (e.g., if the process fails to start)
    _process = subprocess.Popen(
        ["python", "-m", f"{node_type}", node_name, "--port", str(port)] + extra_args,
        stdout=out_file,
        stderr=out_file,
    )


def stop_client(client_config: dict, port: int):
    """
    Stop a client.
    """
    client_name = client_config["name"]
    print(f"Stopping client {client_name} on port {port}")
    stop_node("client", client_name, port)


def stop_hub(hub_config: dict, port: int):
    """
    Stop a hub.
    """
    hub_name = hub_config["name"]
    print(f"Stopping hub {hub_name} on port {port}")
    stop_node("hub", hub_name, port)


def stop_node(node_type: str, node_name: str, port: int):
    """
    Start a node (common processing for hubs and clients).
    """
    # TODO: Error handling
    url = f"http://localhost:{port}/dske/{node_type}/mgmt/v1/stop"
    try:
        _response = requests.post(url, timeout=1.0)
    except requests.exceptions.RequestException as exc:
        print(f"Failed to stop {node_type} {node_name}: {exc}")


def status_client(client_config: dict, port: int):
    """
    Report status for a client.
    """
    client_name = client_config["name"]
    print(f"Status for client {client_name} on port {port}")
    status_node("client", client_name, port)


def status_hub(hub_config: dict, port: int):
    """
    Reports status for a hub.
    """
    hub_name = hub_config["name"]
    print(f"Status for hub {hub_name} on port {port}")
    status_node("hub", hub_name, port)


def status_node(node_type: str, node_name: str, port: int):
    """
    Report status for a node (common processing for hubs and clients).
    """
    # TODO: Error handling
    url = f"http://localhost:{port}/dske/{node_type}/mgmt/v1/status"
    try:
        response = requests.get(url, timeout=1.0)
    except requests.exceptions.RequestException as exc:
        print(f"Failed get status for {node_type} {node_name}: {exc}")
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
