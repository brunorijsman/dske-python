"""
System test for usage of PSRD.
"""

import pytest
from common.signing_key import SIGNING_KEY_SIZE
from . import system_test_common


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
    expected_consumed: int,
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
                            # TODO: For now, assume one block per pool
                            block_status = peer_hub_status[f"{local_or_peer}_pool"][
                                "blocks"
                            ][0]
                            assert block_status["consumed"] == expected_consumed


def _check_hub_psrd_consumption(
    for_hub_name: str,  # * for all clients
    for_peer_client_name: str,  # * for all hubs
    for_local_or_peer: str,
    expected_consumed: int,
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
                            # TODO: For now, assume one block per pool
                            block_status = peer_client_status[f"{local_or_peer}_pool"][
                                "blocks"
                            ][0]
                            assert block_status["consumed"] == expected_consumed


def test_psrd_usage_one_small_key():
    """
    Test PSRD usage when establishing one small key.
    """
    # Check no PSRD consumed at start (out-of-band messages are not signed nor encrypted)
    _check_client_psrd_consumption("*", "*", "*", 0)
    _check_hub_psrd_consumption("*", "*", "*", 0)

    # Get a small key (consume only PSRD from first block)
    key_size_in_bytes = 10
    key_size_in_bits = key_size_in_bytes * 8
    system_test_common.get_key_pair("carol", "cindy", size=key_size_in_bits)

    # Check PSRD consumption on master client Carol
    sign_size = SIGNING_KEY_SIZE
    sign_and_encrypt_size = SIGNING_KEY_SIZE + key_size_in_bytes
    _check_client_psrd_consumption("carol", "*", "local", sign_and_encrypt_size)
    _check_client_psrd_consumption("carol", "*", "peer", sign_size)

    # Check PSRD consumption on slave client Cindy
    _check_client_psrd_consumption("cindy", "*", "local", sign_size)
    _check_client_psrd_consumption("cindy", "*", "peer", sign_and_encrypt_size)

    # Check PSRD consumption on each hub
    for client in ["celia", "connie", "curtis"]:
        _check_hub_psrd_consumption("*", client, "*", 0)
    _check_hub_psrd_consumption("*", "carol", "local", sign_size)
    _check_hub_psrd_consumption("*", "carol", "peer", sign_and_encrypt_size)
    _check_hub_psrd_consumption("*", "cindy", "local", sign_and_encrypt_size)
    _check_hub_psrd_consumption("*", "cindy", "peer", sign_size)
