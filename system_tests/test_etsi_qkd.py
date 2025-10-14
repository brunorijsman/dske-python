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


def test_key_id_not_uuid():
    """
    Get key with key id that is not a uuid (expect error).
    """
    system_test_common.start_topology()
    system_test_common.get_key_with_key_ids(
        "carol", "connie", "not-a-uuid", expected_status_code=400
    )
    system_test_common.stop_topology()
