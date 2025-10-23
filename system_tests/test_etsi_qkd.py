"""
System test for the ETSI QKD API.
"""

import pytest
from . import system_test_common


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """
    Setup and teardown for each test.
    """
    system_test_common.start_topology()
    yield
    system_test_common.stop_topology()


def test_get_status():
    """
    ETSI QKD Get status
    """
    system_test_common.get_status("curtis", "cindy")


def test_get_key_pair():
    """
    ETSI QKD Get key on master, ETSI QKD get key with key IDs on slave.
    """
    system_test_common.get_key_pair("carol", "cindy")


def test_key_id_not_uuid():
    """
    ETSI QKD Get key with key IDs, using a key ID that is not a UUID (expect error).
    """
    system_test_common.get_key_with_key_ids(
        "carol", "connie", "not-a-uuid", expected_status_code=400
    )
