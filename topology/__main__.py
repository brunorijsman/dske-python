"""
Main entry point for the topology package.
"""

import argparse
import requests
import subprocess

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


def parse_command_line_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="DSKE Topology")
    parser.add_argument("configfile", help="Configuration filename")
    parser.add_argument("command", choices=["start", "stop"])
    args = parser.parse_args()
    return args


def start_topology(parsed_config: dict):
    """
    Start the topology.
    """
    port = _BASE_PORT
    for hub_config in parsed_config["hubs"]:
        start_hub(hub_config, port)
        port += 1
    for client_config in parsed_config["clients"]:
        start_client(client_config, port)
        port += 1


def start_hub(hub_config: dict, port: int):
    """
    Start a hub.
    """
    name = hub_config["name"]
    print(f"Starting hub {hub_config['name']} on port {port}")
    start_node("hub", name, port)


def start_client(client_config: dict, port: int):
    """
    Start a client.
    """
    name = client_config["name"]
    print(f"Starting client {name} on port {port}")
    start_node("client", name, port)


def start_node(node_type: str, node_name: str, port: int):
    """
    Start a node (common processing for hubs and clients).
    """
    out_filename = f"{node_type}-{node_name}.out"
    # TODO: Should we be using a context manager here?
    # pylint: disable=consider-using-with
    out_file = open(out_filename, "w", encoding="utf-8")
    # TODO: Error handling (e.g., if the process fails to start)
    _process = subprocess.Popen(
        ["python", "-m", f"{node_type}", node_name, "--port", str(port)],
        stdout=out_file,
        stderr=out_file,
    )


def stop_topology(parsed_config: dict):
    """
    Stop the topology.
    """
    port = _BASE_PORT
    for hub_config in parsed_config["hubs"]:
        stop_hub(hub_config, port)
        port += 1
    for client_config in parsed_config["clients"]:
        stop_client(client_config, port)
        port += 1


def stop_client(client_config: dict, port: int):
    """
    Stop a client.
    """
    print(f"Stopping client {client_config['name']} on port {port}")
    stop_node("client", port)


def stop_hub(hub_config: dict, port: int):
    """
    Stop a hub.
    """
    print(f"Stopping hub {hub_config['name']} on port {port}")
    stop_node("hub", port)


def stop_node(node_type: str, port: int):
    """
    Start a node (common processing for hubs and clients).
    """
    # TODO: Error handling
    url = f"http://localhost:{port}/dske/{node_type}/mgmt/v1/stop"
    _response = requests.post(url)


if __name__ == "__main__":
    main()
