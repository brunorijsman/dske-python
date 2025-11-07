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
    # For Get Key with key IDs, we need to call the API directly using HTTPX instead of using
    # the manager to set a wrong master SAE ID.
    connie_port = 8108
    url = (
        f"http://127.0.0.1:{connie_port}"
        f"/client/connie/etsi/api/v1/keys/serena/dec_keys?"  # Serena is wrong master SAE ID
        f"key_ID={key_id}"
    )
    result = httpx.get(url, headers={"Authorization": "sofia"})
    assert result.status_code == 400
    assert "Master SAE ID does not match" in result.text


def test_wrong_slave_sae_id_correct_client():
    """
    ETSI QKD Get key with key IDs, using a slave SAE ID that does not match the slave SAE ID
    that was used in the Get key call (expect error). The slave SAE ID is wrong, but connected to
    the correct client.
    """
    key_id = system_test_common.get_key("sam", "sunny")
    assert key_id is not None
    # For Get Key with key IDs, we need to call the API directly using HTTPX instead of using
    # the manager to set a wrong master SAE ID.
    curtis_port = 8109
    url = (
        f"http://127.0.0.1:{curtis_port}"
        f"/client/curtis/etsi/api/v1/keys/sam/dec_keys?"  # All correct
        f"key_ID={key_id}"
    )
    # Susan is wrong slave SAE ID, but connected to correct client (KME), so the client will
    # accept the request and attempt to gather the shares.
    result = httpx.get(url, headers={"Authorization": "susan"})
    assert result.status_code == 400
    assert "Slave SAE ID does not match" in result.text


def test_get_key_master_sae_not_connected_to_client():
    """
    Invoke ETSI QKD Get key with key IDs on the wrong client (KME) for the given master SAE ID
    (expect error).
    """
    carol_port = 8105
    url = (
        f"http://127.0.0.1:{carol_port}"
        f"/client/carol/etsi/api/v1/keys/sam/enc_keys"  # All correct
    )
    result = httpx.get(
        url, headers={"Authorization": "sunny"}
    )  # SAE sunny not connected to Carol
    assert result.status_code == 400
    assert "Encryptor is not connected to client" in result.text


def test_get_key_with_key_ids_slave_sae_not_connected_to_client():
    """
    Invoke ETSI QKD Get key with key IDs on the wrong client (KME) for the given slave SAE ID
    (expect error).
    """
    key_id = system_test_common.get_key("sam", "serena")
    assert key_id is not None
    curtis_port = 8109
    url = (
        f"http://127.0.0.1:{curtis_port}"
        f"/client/curtis/etsi/api/v1/keys/sam/dec_keys?"  # Curtis is wrong client (KME) for Serena
        f"key_ID={key_id}"
    )
    result = httpx.get(url, headers={"Authorization": "serena"})
    assert result.status_code == 400
    assert "Encryptor is not connected to client" in result.text
