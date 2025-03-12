"""
A DSKE client.
"""

import os

import common

from key import UserKey
from .peer_hub import PeerHub

# TODO: Make this configurable
_MIN_NR_SHARES = 3  # The minimum number of key shares required to reconstruct the key.


class Client:
    """
    A DSKE client.
    """

    _min_key_size_in_bits = 1
    _max_key_size_in_bits = 100_000  # TODO: Pick a value
    _default_key_size_in_bits = 128
    _max_stored_key_count = 1000  # TODO: What is a sensible value?
    _max_keys_per_request = 1  # TODO: Allow more than one

    _client_name: str
    _peer_hubs: list[PeerHub]

    def __init__(self, name: str, peer_hub_urls: list[str]):
        self._client_name = name
        self._peer_hubs = []
        for peer_hub_url in peer_hub_urls:
            peer_hub = PeerHub(self, peer_hub_url)
            self._peer_hubs.append(peer_hub)

    @property
    def name(self):
        """
        Get the client name.
        """
        return self._client_name

    def to_mgmt_dict(self):
        """
        Get the management status.
        """
        peer_hubs_status = [peer_hub.to_mgmt_dict() for peer_hub in self._peer_hubs]
        return {"client_name": self._client_name, "peer_hubs": peer_hubs_status}

    async def etsi_status(self, slave_sae_id: str):
        """
        ETSI QKD 014 V1.1.1 Status API.
        """
        # See remark about ETSI QKD API in file TODO
        return {
            "source_kme_id": self._client_name,
            "target_kme_id": slave_sae_id,
            "master_sae_id": self._client_name,
            "slave_sae_id": slave_sae_id,
            "key_size": self._default_key_size_in_bits,
            "stored_key_count": 25000,  # TODO
            "max_key_count": self._max_stored_key_count,
            "max_key_per_request": self._max_keys_per_request,
            "max_key_size": self._max_key_size_in_bits,
            "min_key_size": self._min_key_size_in_bits,
            "max_sae_id_count": 0,  # TODO: Add support for key multicast
        }

    async def etsi_get_key(self, _slave_sae_id: str):
        """
        ETSI QKD 014 V1.1.1 Get Key API.
        """
        # TODO: Store the _slave_sae_id somewhere. It should be used to determine who is allowed
        #       to retrieve the key on the other side by calling Get Key with Key IDs.
        #       Perhaps also store the master_sae_id to keep track of who the initiator/master is.
        # See remarks about ETSI QKD API in file TODO
        assert self._default_key_size_in_bits % 8 == 0
        size_in_bytes = self._default_key_size_in_bits // 8
        user_key = UserKey.create_random_user_key(size_in_bytes)
        # TODO: Error handling; this the sharing amongst peer hubs could fail.
        await self.scatter_user_key_amongst_peer_hubs(user_key)
        return {
            "keys": {
                "key_ID": user_key.user_key_uuid,
                "key": common.bytes_to_str(user_key.value),
            }
        }

    async def etsi_get_key_with_key_ids(self, _slave_sae_id: str, key_id: str):
        """
        ETSI QKD 014 V1.1.1 Get Key API.
        """
        # TODO: key_id should be a list; allow to get more than one key in a single call.
        # TODO: Error handling; the gather could fail for any number of reasons.
        user_key = await self.gather_user_key_from_peer_hubs()
        return {
            "keys": [
                {
                    "key_ID": user_key.user_key_uuid,
                    "key": common.bytes_to_str(user_key.value),
                }
            ]
        }

    async def register_with_all_peer_hubs(self) -> None:
        """
        Register to all peer hubs.
        """
        for peer_hub in self._peer_hubs:
            await peer_hub.register()

    async def unregister_from_all_peer_hubs(self) -> None:
        """
        Unregister from all peer hubs.
        """
        for peer_hub in self._peer_hubs:
            await peer_hub.unregister()

    async def request_psrd_from_all_peer_hubs(self) -> None:
        """
        Request PSRD from all peer hubs.
        """
        for peer_hub in self._peer_hubs:
            await peer_hub.request_psrd()

    async def scatter_user_key_amongst_peer_hubs(self, user_key: UserKey) -> None:
        """
        Split the user key into user key shares, and send each user key share to a peer hub.
        """
        # Split user key into shares
        nr_shares = len(self._peer_hubs)
        user_key_shares = user_key.split_into_user_key_shares(nr_shares, _MIN_NR_SHARES)
        # Allocate encryption and authentication keys for each share
        for peer_hub, user_key_share in zip(self._peer_hubs, user_key_shares):
            peer_hub.allocate_encryption_and_authentication_psrd_keys_for_user_key_share(
                user_key_share
            )
        # TODO: Error handling. If there was an issue allocating any one of the encryption or
        #       authentication keys, deallocate all of the ones that were allocated, and return
        #       and error to the caller.
        # Consume the allocated encryption and authentication keys for each share
        for user_key_share in user_key_shares:
            user_key_share.consume_encryption_and_authentication_psrd_keys()
        # POST the user key shares to the peer hubs
        for peer_hub, user_key_share in zip(self._peer_hubs, user_key_shares):
            await peer_hub.post_key_share(user_key_share)
        # Delete folly consumed blocks from all pools
        for peer_hub in self._peer_hubs:
            peer_hub.delete_fully_consumed_psrd_blocks()

    async def gather_user_key_from_peer_hubs(self) -> UserKey:
        """
        Gather user key shares from the peer hubs, and reconstruct the user key out of (a subset of)
        the user key shares.
        """
        # TODO: Continue from here
        # TODO: Send a get key-share to each peer hub (this is allowed to fail)
        # TODO: Decrypt each share
        # TODO: Verify the signature of each share
        # TODO: Check if we have enough shares
        # TODO: Reconstruct the user key using Shamir secret sharing algorithm
        # TODO: Return the user key
