"""
System test for the ETSI QKD API.
"""

import uuid
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


def test_get_status():
    """
    ETSI QKD Get status
    """
    system_test_common.get_status("sam", "sofia")


def test_get_key_pair_simple():
    """
    ETSI QKD Get key on master, ETSI QKD get key with key IDs on slave.
    """
    system_test_common.get_key_pair("sam", "sunny")


def test_get_key_pair_non_default_size():
    """
    Get key pair with non-default size.
    """
    system_test_common.get_key_pair("serena", "susan", size=1024)


def test_key_id_not_uuid():
    """
    ETSI QKD Get key with key IDs, using a key ID that is not a UUID (expect error).
    """
    system_test_common.get_key_with_key_ids(
        "sam", "sofia", "not-a-uuid", expected_status_code=400
    )


def test_wrong_key_id():
    """
    ETSI QKD Get key with key IDs, using a key ID that was not returned by Get Key (expect error).
    """
    key_id = system_test_common.get_key("sam", "sofia")
    assert key_id is not None
    wrong_uuid = str(uuid.uuid4())
    system_test_common.get_key_with_key_ids(
        "sam", "sofia", wrong_uuid, expected_status_code=400
    )


def test_wrong_master_sae_id():
    """
    ETSI QKD Get ey with key IDs, using a master SAE ID that does not match the master SAE ID
    that was used in the Get key call (expect error).
    """
    key_id = system_test_common.get_key("sam", "sofia")
    assert key_id is not None
    connie_port = 8108
    url = (
        f"http://127.0.0.1:{connie_port}"
        f"/client/connie/etsi/api/v1/keys/wrong_master_sae_id/dec_keys?"
        f"key_ID={key_id}"
    )
    result = httpx.get(url, headers={"Authorization": "sofia"})
    assert result.status_code == 400
    assert "Master SAE ID does not match" in result.text


# def test_wrong_slave_sae_id():
#     """
#     ETSI QKD Get ey with key IDs, using a master SAE ID that does not match the master SAE ID
#     that was used in the Get key call (expect error).
#     """
#     key_id = system_test_common.get_key("sam", "sofia")
#     assert key_id is not None
#     connie_port = 8108
#     url = (
#         f"http://127.0.0.1:{connie_port}/client/connie/etsi/api/v1/keys/sunny/dec_keys?"
#         f"key_ID={key_id}"
#     )
#     result = httpx.get(url)
#     assert result.status_code == 400
#     assert "Master SAE ID does not match" in result.text
