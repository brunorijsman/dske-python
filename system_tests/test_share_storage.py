"""
Test share storage at hubs.
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


def test_get_key_creates_shares_on_hubs():
    """
    Test that getting a key on the master client results in shares being created on the hubs.
    """
    key_id = system_test_common.get_key("sam", "sofia")
    status = system_test_common.status_node("hub", "hank")
    assert "shares" in status
    shares = status["shares"]
    assert len(shares) == 1
    share = shares[0]
    assert share["key_id"] == key_id
    assert share["master_sae_id"] == "sam"
    assert share["slave_sae_id"] == "sofia"
    assert share["share_index"] == 0
