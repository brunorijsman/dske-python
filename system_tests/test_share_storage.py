"""
Test share storage at hubs.
"""

from time import sleep
import httpx
import pytest
from common.configuration import DEFAULT_SHARE_TIMEOUT_SECS
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
    Test that getting a key on the master client results in shares being created on the hubs,
    and that getting a with with key IDs on the slave client removes the shares (normally, unless
    the slave SAE ID is incorrect).
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


def test_shares_on_hubs_timeout():
    """
    Test that shares are removed from hubs after their timeout expires (i.e. the slave client
    does not get the key with key IDs in time).
    """
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
    # Wait for share to timeout
    sleep(DEFAULT_SHARE_TIMEOUT_SECS + 10)
    # The share should be removed from the hub
    status = system_test_common.status_node("hub", "hank")
    assert "shares" in status
    shares = status["shares"]
    assert len(shares) == 0
