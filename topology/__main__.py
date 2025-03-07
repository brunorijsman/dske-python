"""
Main entry point for the topology package.
"""

import argparse
import config

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
    for client_config in parsed_config["clients"]:
        start_client(client_config, port)
        port += 1
    for hub_config in parsed_config["hubs"]:
        start_hub(hub_config, port)
        port += 1


def start_client(client_config: dict, port: int):
    """
    Start a client.
    """
    print(f"Starting client {client_config['name']} on port {port}")


def start_hub(hub_config: dict, port: int):
    """
    Start a hub.
    """
    print(f"Starting hub {hub_config['name']} on port {port}")


def stop_topology(parsed_config: dict):
    """
    Stop the topology.
    """
    port = _BASE_PORT
    for client_config in parsed_config["clients"]:
        stop_client(client_config, port)
        port += 1
    for hub_config in parsed_config["hubs"]:
        stop_hub(hub_config, port)
        port += 1


def stop_client(client_config: dict, port: int):
    """
    Stop a client.
    """
    print(f"Stopping client {client_config['name']} on port {port}")


def stop_hub(hub_config: dict, port: int):
    """
    Stop a hub.
    """
    print(f"Stopping hub {hub_config['name']} on port {port}")


if __name__ == "__main__":
    main()
