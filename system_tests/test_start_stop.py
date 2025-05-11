"""
System test for starting and stopping nodes.
"""

from system_test_common import start_topology, stop_topology


def test_start_stop_nodes():
    """
    Start all nodes, then stop all nodes.
    """
    start_topology()
    stop_topology()
