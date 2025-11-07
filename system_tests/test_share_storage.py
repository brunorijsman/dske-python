"""
Test share storage at hubs.
"""

import httpx
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


def test_shares_on_hubs():
    """
    Test that getting a key on the master client results in shares being created on the hubs.
    """
    # Pylint complains this looks too much like test_etsi_qkd
    # pylint: disable=duplicate-code
    # Get key on master client
    key_id = system_test_common.get_key("sam", "sunny")
    # There should be a share stored one each hub (we only check hank)
    status = system_test_common.status_node("hub", "hank")
    assert "shares" in status
    shares = status["shares"]
    assert len(shares) == 1
    share = shares[0]
    assert share["key_id"] == key_id
    assert share["master_sae_id"] == "sam"
    assert share["slave_sae_id"] == "sunny"
    assert share["share_index"] == 0
    # Incorrect get key with key IDS on slave client (wrong master SAE ID)
    curtis_port = 8109
    url = (
        f"http://127.0.0.1:{curtis_port}"
        f"/client/curtis/etsi/api/v1/keys/sam/dec_keys?"  # All correct
        f"key_ID={key_id}"
    )
    result = httpx.get(url, headers={"Authorization": "susan"})  # Wrong slave SAE ID
    assert result.status_code == 400
    assert "Slave SAE ID does not match" in result.text
    # Share was not removed
    status = system_test_common.status_node("hub", "hank")
    assert "shares" in status
    shares = status["shares"]
    assert len(shares) == 1
    # Correct get key with key IDS on slave client
    system_test_common.get_key_with_key_ids("sam", "sunny", key_id)
    # The share should be removed from the hub
    status = system_test_common.status_node("hub", "hank")
    assert "shares" in status
    shares = status["shares"]
    assert len(shares) == 0
