"""
Main entry point for the topology package.
"""

import argparse
import config


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
    for client_config in parsed_config["clients"]:
        start_client(client_config)
    for hub_config in parsed_config["hubs"]:
        start_hub(hub_config)


def start_client(client_config: dict):
    """
    Start a client.
    """
    print(f"Starting client {client_config['name']}")


def start_hub(hub_config: dict):
    """
    Start a hub.
    """
    print(f"Starting hub {hub_config['name']}")


def stop_topology(parsed_config: dict):
    """
    Stop the topology.
    """
    for client_config in parsed_config["clients"]:
        stop_client(client_config)
    for hub_config in parsed_config["hubs"]:
        stop_hub(hub_config)


def stop_client(client_config: dict):
    """
    Stop a client.
    """
    print(f"Stopping client {client_config['name']}")


def stop_hub(hub_config: dict):
    """
    Stop a hub.
    """
    print(f"Stopping hub {hub_config['name']}") 

    
if __name__ == "__main__":
    main()
