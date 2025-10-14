"""
System test for node failures.
"""

from . import system_test_common


def test_less_than_k_node_failures_before_get_key():
    """
    Less than k node failures before the initial Get Key request; key establishment should succeed.
    """
    system_test_common.start_topology()
    system_test_common.stop_node("hub", "helen")
    system_test_common.get_key_pair("celia", "curtis")
    system_test_common.stop_topology(not_started_node=("hub", "helen"))
