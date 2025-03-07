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
    _parsed_config = config.parse_configuration(args.configfile)


def parse_command_line_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="DSKE Topology")
    parser.add_argument("configfile", help="Configuration filename")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
