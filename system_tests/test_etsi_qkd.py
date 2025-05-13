"""
System test for the ETSI QKD API.
"""

from . import system_test_common


def test_get_key_pair():
    """
    Get key on master, get key with key id on slave.
    """
    system_test_common.start_topology()
    system_test_common.get_key_pair("carol", "cindy")
    system_test_common.stop_topology()
