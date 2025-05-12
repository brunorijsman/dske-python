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
    Start all nodes, then stop all nodes.
    """
    system_test_common.start_topology()
    _status = system_test_common.status_topology()
    system_test_common.stop_topology()
