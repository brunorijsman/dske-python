"""
System test for usage of PSRD.
"""

import sys
import pytest
from . import system_test_common


_CLIENTS = ["carol", "celia", "cindy", "connie", "curtis"]
_HUBS = ["hank", "helen", "hilary", "holly", "hugo"]
_AUTHENTICATION_KEY_SIZE_IN_BYTES = 4

_START_REQUEST_PSRD_THRESHOLD = 500
_STOP_REQUEST_PSRD_THRESHOLD = 2000
_GET_PSRD_BLOCK_SIZE = 2000


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """
    Setup and teardown for each test.
    """
    system_test_common.start_topology()
    yield
    system_test_common.stop_topology()


def _client_peer_hub_status(client_name: str, hub_name: str):
    topology_status = system_test_common.status_topology()
    client_status = topology_status[("client", client_name)]
    peer_hub_status = next(
        (ph for ph in client_status["peer_hubs"] if ph["hub_name"] == hub_name),
        None,
    )
    return peer_hub_status


def _client_block_status(client_name: str, hub_name: str, local_or_peer: str):
    assert local_or_peer in ("local", "peer")
    # TODO: For now, assume there is only one local block
    peer_hub_status = _client_peer_hub_status(client_name, hub_name)
    print(f"{peer_hub_status=}", file=sys.stderr)

    block_status = peer_hub_status[f"{local_or_peer}_pool"]["blocks"][0]
    return block_status


def _check_client_psrd_consumption(
    for_client_name: str,  # * for all clients
    for_hub_name: str,  # * for all hubs
    local_or_peer: str,
    expected_consumed: int,
):
    for client_name in _CLIENTS:
        for hub_name in _HUBS:
            if client_name in ("*", for_client_name):
                if hub_name in ("*", for_hub_name):
                    block_status = _client_block_status(
                        client_name, hub_name, local_or_peer
                    )
                    assert block_status["consumed"] == expected_consumed


def test_psrd_usage_one_small_key():
    """
    Test PSRD usage when establishing one small key.
    """
    # Check no PSRD consumed before getting key
    _check_client_psrd_consumption("*", "*", "local", 0)

    # Get a small key (consume only PSRD from first block)
    key_size_in_bytes = 10
    key_size_in_bits = key_size_in_bytes * 8
    system_test_common.get_key_pair("carol", "cindy", size=key_size_in_bits)

    # Check PSRD consumption on master client Carol
    local_consumed = _AUTHENTICATION_KEY_SIZE_IN_BYTES + key_size_in_bytes
    _check_client_psrd_consumption("carol", "*", "local", local_consumed)
    peer_consumed = _AUTHENTICATION_KEY_SIZE_IN_BYTES
    _check_client_psrd_consumption("carol", "*", "peer", peer_consumed)

    # Check PSRD consumption on slave client Cindy
    local_consumed = _AUTHENTICATION_KEY_SIZE_IN_BYTES
    _check_client_psrd_consumption("cindy", "*", "local", local_consumed)
    peer_consumed = _AUTHENTICATION_KEY_SIZE_IN_BYTES + key_size_in_bytes
    _check_client_psrd_consumption("cindy", "*", "peer", peer_consumed)
