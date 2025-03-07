"""
Configuration file parser for the topology module.
"""

import pprint
import sys
import cerberus
import yaml

_HUB_SCHEMA =  {
    'type': 'dict',
    'schema': {
        'name': {'type': 'string'},
    }
}

_CLIENT_SCHEMA =  {
    'type': 'dict',
    'schema': {
        'name': {'type': 'string'},
    }
}

_SCHEMA = {
    'hubs': {
        'type': 'list',
        'schema': _HUB_SCHEMA
    },
    'clients': {
        'type': 'list',
        'schema': _CLIENT_SCHEMA
    }
}

def parse_configuration(filename: str) -> dict:
    """
    Parse the configuration file and return the configuration.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            try:
                config = yaml.safe_load(file)
            except yaml.YAMLError as err:
                print(f"Could not load configuration file {filename}: {str(err)}", file=sys.stderr)
                sys.exit(1)
    except (OSError, IOError) as err:
        print(f"Could not open configuration file {filename} ({err})", file=sys.stderr)
        sys.exit(1)
    validator = cerberus.Validator()
    if not validator.validate(config, _SCHEMA):
        print(f"Could not parse configuration file {filename}", file=sys.stderr)
        pretty_printer = pprint.PrettyPrinter()
        pretty_printer.pprint(validator.errors)
        sys.exit(1)
    config = validator.normalized(config)
    return config
