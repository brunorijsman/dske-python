"""
Common functions for the system tests.
"""

from subprocess import Popen
from time import sleep


_DEFAULT_TOPOLOGY_FILE = "topology.yaml"
_NODE_START_DELAY = 1.0


def start_topology(topology_file=_DEFAULT_TOPOLOGY_FILE):
    """
    Start a topology.
    """
    args = [topology_file, "start"]
    _run_manager(args)
    sleep(_NODE_START_DELAY)


def stop_topology(topology_file=_DEFAULT_TOPOLOGY_FILE):
    """
    Stop a topology.
    """
    args = [topology_file, "stop"]
    _run_manager(args)


def _run_manager(args):
    """
    Run the manager.
    """
    # TODO: Append to file system_test.out instead of overwriting on each run
    out_filename = "system_test.out"
    with open(out_filename, "w", encoding="utf-8") as out_file:
        with Popen(
            ["python", "-m", "manager"] + args,
            stdout=out_file,
            stderr=out_file,
        ) as _process:
            pass
