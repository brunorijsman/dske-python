"""
System test for starting and stopping nodes.
"""

import system_test_common


def test_start_stop():
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
    Starting the nodes twice without stopping them in between should produce an error message.
    """
    system_test_common.start_topology()
    # Starting the nodes again should produce an error message
    # TODO: Implement this
    system_test_common.start_topology()
    # Stop the nodes to clean up for the next test
    system_test_common.stop_topology()
