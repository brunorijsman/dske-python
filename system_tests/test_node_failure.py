"""
System test for node failures.
"""

from . import system_test_common


def test_one_node_failure_before_get_key():
    """
    One node failure before the initial Get Key request.
    Four nodes remain, which is greater than k=3.
    Key establishment should succeed.
    """
    system_test_common.start_topology()
    system_test_common.stop_node("hub", "helen")
    system_test_common.get_key_pair("celia", "curtis")
    system_test_common.stop_topology(stopped_nodes=[("hub", "helen")])


def test_two_node_failures_before_get_key():
    """
    Two node failures before the initial Get Key request.
    Three nodes remain, which is equal to k=3.
    Key establishment should succeed.
    """
    system_test_common.start_topology()
    system_test_common.stop_node("hub", "helen")
    system_test_common.stop_node("hub", "hugo")
    system_test_common.get_key_pair("carol", "connie")
    system_test_common.stop_topology(stopped_nodes=[("hub", "helen"), ("hub", "hugo")])


def test_three_node_failures_before_get_key():
    """
    Three node failures before the initial Get Key request.
    Two nodes remain, which is less than k=3.
    Key establishment should fail.
    """
    system_test_common.start_topology()
    system_test_common.stop_node("hub", "hank")
    system_test_common.stop_node("hub", "helen")
    system_test_common.stop_node("hub", "hugo")
    # TODO: Expect failure on initial Get Key request
    system_test_common.get_key_pair("carol", "connie")
    system_test_common.stop_topology(
        stopped_nodes=[("hub", "helen"), ("hub", "hugo"), ("hub", "harry")]
    )
