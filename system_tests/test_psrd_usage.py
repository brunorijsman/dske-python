"""
System test for usage of PSRD.
"""

from time import sleep
from typing import List
import pytest
from common.signing_key import SIGNING_KEY_SIZE
from client.peer_hub import START_REQUEST_PSRD_THRESHOLD
from . import system_test_common


# The test cases here assume the following parameters defined in client/peer_hub.py. If these
# values are changed significantly, the test cases here may have to be updated accordingly.
#
# START_REQUEST_PSRD_THRESHOLD = 500
# STOP_REQUEST_PSRD_THRESHOLD = 2000
# GET_PSRD_BLOCK_SIZE = 2000


_CLIENTS = ["carol", "celia", "cindy", "connie", "curtis"]
_HUBS = ["hank", "helen", "hilary", "holly", "hugo"]


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """
    Setup and teardown for each test.
    """
    system_test_common.start_topology()
    yield
    system_test_common.stop_topology()


def _check_client_psrd_consumption(
    for_client_name: str,  # * for all clients
    for_peer_hub_name: str,  # * for all hubs
    for_local_or_peer: str,
    expected_used_lst: List[int],
):
    """
    Check the PSRD consumption for a given pool (local or remote) on a given (or all) client(s)
    for a given (or all) peer hub(s).
    """
    # pylint: disable=too-many-nested-blocks
    topology_status = system_test_common.status_topology()
    for client_name in _CLIENTS:
        if for_client_name in ("*", client_name):
            client_status = topology_status[("client", client_name)]
            for peer_hub_name in _HUBS:
                if for_peer_hub_name in ("*", peer_hub_name):
                    peer_hub_status = [
                        ph
                        for ph in client_status["peer_hubs"]
                        if ph["hub_name"] == peer_hub_name
                    ][0]
                    for local_or_peer in ("local", "peer"):
                        if for_local_or_peer in ("*", local_or_peer):
                            block_statuses = peer_hub_status[f"{local_or_peer}_pool"][
                                "blocks"
                            ]
                            assert len(block_statuses) == len(expected_used_lst)
                            for block_status, expected_used in zip(
                                block_statuses, expected_used_lst
                            ):
                                assert block_status["nr_used_bytes"] == expected_used


def _check_hub_psrd_consumption(
    for_hub_name: str,  # * for all clients
    for_peer_client_name: str,  # * for all hubs
    for_local_or_peer: str,
    expected_used_lst: List[int],
):
    """
    Check the PSRD consumption for a given pool (local or remote) on a given (or all) client(s)
    for a given (or all) peer hub(s).
    """
    # pylint: disable=too-many-nested-blocks
    topology_status = system_test_common.status_topology()
    for hub_name in _HUBS:
        if for_hub_name in ("*", hub_name):
            hub_status = topology_status[("hub", hub_name)]
            for peer_client_name in _CLIENTS:
                if for_peer_client_name in ("*", peer_client_name):
                    peer_client_status = [
                        pc
                        for pc in hub_status["peer_clients"]
                        if pc["client_name"] == peer_client_name
                    ][0]
                    for local_or_peer in ("local", "peer"):
                        if for_local_or_peer in ("*", local_or_peer):
                            block_statuses = peer_client_status[
                                f"{local_or_peer}_pool"
                            ]["blocks"]
                            assert len(block_statuses) == len(expected_used_lst)
                            for block_status, expected_used in zip(
                                block_statuses, expected_used_lst
                            ):
                                assert block_status["nr_used_bytes"] == expected_used


def test_psrd_usage_one_small_key():
    """
    Test PSRD usage when establishing one small key (small enough to fit in one block).
    """
    # Check no PSRD used at start (out-of-band messages are not signed nor encrypted)
    _check_client_psrd_consumption("*", "*", "*", [0])
    _check_hub_psrd_consumption("*", "*", "*", [0])

    # Get a small key (consume only PSRD from first block)
    key_size_in_bytes = 10
    key_size_in_bits = key_size_in_bytes * 8
    system_test_common.get_key_pair("sammy", "sofia", size=key_size_in_bits)

    # Check PSRD consumption on master client carol
    sign_size = SIGNING_KEY_SIZE
    sign_and_encrypt_size = SIGNING_KEY_SIZE + key_size_in_bytes
    _check_client_psrd_consumption("carol", "*", "local", [sign_and_encrypt_size])
    _check_client_psrd_consumption("carol", "*", "peer", [sign_size])

    # Check PSRD consumption on slave client connie
    _check_client_psrd_consumption("connie", "*", "local", [sign_size])
    _check_client_psrd_consumption("connie", "*", "peer", [sign_and_encrypt_size])

    # Check PSRD consumption on each hub
    for client in ["celia", "connie", "curtis"]:
        _check_hub_psrd_consumption("*", client, "*", [0])
    _check_hub_psrd_consumption("*", "carol", "local", [sign_size])
    _check_hub_psrd_consumption("*", "carol", "peer", [sign_and_encrypt_size])
    _check_hub_psrd_consumption("*", "connie", "local", [sign_and_encrypt_size])
    _check_hub_psrd_consumption("*", "connie", "peer", [sign_size])


def test_psrd_usage_two_small_keys():
    """
    Test PSRD usage when establishing two small keys (small enough for both keys to fit in one
    block).
    """
    # Check no PSRD used at start (out-of-band messages are not signed nor encrypted)
    _check_client_psrd_consumption("*", "*", "*", [0])
    _check_hub_psrd_consumption("*", "*", "*", [0])

    # Get two small keys (consume only PSRD from first block)
    key_1_size_in_bytes = 10
    key_1_size_in_bits = key_1_size_in_bytes * 8
    system_test_common.get_key_pair("carol", "cindy", size=key_1_size_in_bits)
    key_2_size_in_bytes = 15
    key_2_size_in_bits = key_2_size_in_bytes * 8
    system_test_common.get_key_pair("carol", "cindy", size=key_2_size_in_bits)

    # Check PSRD consumption on master client Carol
    sign_size = 2 * SIGNING_KEY_SIZE
    sign_and_encrypt_size = (
        2 * SIGNING_KEY_SIZE + key_1_size_in_bytes + key_2_size_in_bytes
    )
    _check_client_psrd_consumption("carol", "*", "local", [sign_and_encrypt_size])
    _check_client_psrd_consumption("carol", "*", "peer", [sign_size])

    # Check PSRD consumption on slave client Cindy
    _check_client_psrd_consumption("cindy", "*", "local", [sign_size])
    _check_client_psrd_consumption("cindy", "*", "peer", [sign_and_encrypt_size])

    # Check PSRD consumption on each hub
    for client in ["celia", "connie", "curtis"]:
        _check_hub_psrd_consumption("*", client, "*", [0])
    _check_hub_psrd_consumption("*", "carol", "local", [sign_size])
    _check_hub_psrd_consumption("*", "carol", "peer", [sign_and_encrypt_size])
    _check_hub_psrd_consumption("*", "cindy", "local", [sign_and_encrypt_size])
    _check_hub_psrd_consumption("*", "cindy", "peer", [sign_size])


def test_psrd_usage_refresh():
    """
    Test PSRD usage when establishing one key, large enough to cause the pool size to drop below
    the threshold for requesting more PSRD. To be more precise:
    - Any pool from which both a signing key and an encryption key are allocated requests a new
      block. The first block will be partly used. The second block will have nothing used.
    - Any pool from which only a signing key is allocated does not request a new block.
    """
    # Check no PSRD used at start (out-of-band messages are not signed nor encrypted)
    _check_client_psrd_consumption("*", "*", "*", [0])
    _check_hub_psrd_consumption("*", "*", "*", [0])

    # Get a large key (triggering PSRD refresh)
    key_size_in_bytes = 1600
    key_size_in_bits = key_size_in_bytes * 8
    system_test_common.get_key_pair("carol", "cindy", size=key_size_in_bits)

    # Giver refresh time to complete
    sleep(1.0)

    # Check PSRD consumption on master client Carol
    sign_size = SIGNING_KEY_SIZE
    sign_and_encrypt_size = SIGNING_KEY_SIZE + key_size_in_bytes
    assert sign_size < START_REQUEST_PSRD_THRESHOLD
    assert sign_and_encrypt_size > START_REQUEST_PSRD_THRESHOLD
    _check_client_psrd_consumption("carol", "*", "local", [sign_and_encrypt_size, 0])
    _check_client_psrd_consumption("carol", "*", "peer", [sign_size])

    # Check PSRD consumption on slave client Cindy
    _check_client_psrd_consumption("cindy", "*", "local", [sign_size])
    _check_client_psrd_consumption("cindy", "*", "peer", [sign_and_encrypt_size, 0])

    # Check PSRD consumption on each hub
    for client in ["celia", "connie", "curtis"]:
        _check_hub_psrd_consumption("*", client, "*", [0])
    _check_hub_psrd_consumption("*", "carol", "local", [sign_size])
    _check_hub_psrd_consumption("*", "carol", "peer", [sign_and_encrypt_size, 0])
    _check_hub_psrd_consumption("*", "cindy", "local", [sign_and_encrypt_size, 0])
    _check_hub_psrd_consumption("*", "cindy", "peer", [sign_size])
