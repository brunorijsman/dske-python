"""
System test for starting and stopping nodes.
"""

from . import system_test_common


def test_start_stop_only():
    """
    Start all nodes, then stop all nodes.
    """
    system_test_common.start_topology()
    system_test_common.stop_topology()


def test_start_status_stop():
    """
    Start all nodes, get status for all nodes, then stop all nodes.
    """
    system_test_common.start_topology()
    _status = system_test_common.status_topology()
    system_test_common.stop_topology()


def test_start_twice():
    """
    Starting the nodes twice without stopping them in between produces an error message.
    """
    system_test_common.start_topology()
    system_test_common.start_topology(already_started=True)
    system_test_common.stop_topology()


def test_stop_without_start():
    """
    Stopping the nodes without starting them first produces an error message.
    """
    system_test_common.stop_topology(not_started=True)
