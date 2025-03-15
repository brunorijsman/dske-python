"""
A DSKE client.
"""

from uuid import UUID
from common import bytes_to_str, Key, reconstruct_binary_secret_from_shares
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

    _name: str
    _peer_hubs: list[PeerHub]

    def __init__(self, name: str, peer_hub_urls: list[str]):
        self._name = name
        self._peer_hubs = []
        for peer_hub_url in peer_hub_urls:
            peer_hub = PeerHub(self, peer_hub_url)
            self._peer_hubs.append(peer_hub)

    @property
    def name(self):
        """
        Get the client name.
        """
        return self._name

    def to_mgmt(self):
        """
        Get the management status.
        """
        peer_hubs_status = [peer_hub.to_mgmt() for peer_hub in self._peer_hubs]
        return {"client_name": self._name, "peer_hubs": peer_hubs_status}

    async def etsi_status(self, slave_sae_id: str):
        """
        ETSI QKD 014 V1.1.1 Status API.
        """
        # See remark about ETSI QKD API in file TODO
        return {
            "source_kme_id": self._name,
            "target_kme_id": slave_sae_id,
            "master_sae_id": self._name,
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
        key = Key.create_random_key(size_in_bytes)
        # TODO: Error handling; this the sharing amongst peer hubs could fail.
        await self.scatter_key_amongst_peer_hubs(key)
        return {
            "keys": {
                "key_ID": key.key_uuid,
                "key": bytes_to_str(key.value),
            }
        }

    async def etsi_get_key_with_key_ids(self, _slave_sae_id: str, key_id: str):
        """
        ETSI QKD 014 V1.1.1 Get Key API.
        """
        # TODO: key_id should be a list; allow to get more than one key in a single call.
        # TODO: Error handling; the gather could fail for any number of reasons.
        key_uuid = UUID(key_id)
        key = await self.gather_key_from_peer_hubs(key_uuid)
        return {
            "keys": [
                {
                    "key_ID": key.key_uuid,
                    "key": bytes_to_str(key.value),
                }
            ]
        }

    async def register_with_all_peer_hubs(self) -> None:
        """
        Register with all peer hubs.
        """
        for peer_hub in self._peer_hubs:
            await peer_hub.register()

    async def unregister_from_all_peer_hubs(self) -> None:
        """
        Unregister from all peer hubs.
        """
        for peer_hub in self._peer_hubs:
            await peer_hub.unregister()

    async def request_block_from_all_peer_hubs(self) -> None:
        """
        Request PSRD from all peer hubs.
        """
        for peer_hub in self._peer_hubs:
            await peer_hub.request_psrd()

    async def scatter_key_amongst_peer_hubs(self, key: Key) -> None:
        """
        Split the key into key shares, and send each key share to a peer hub.
        """
        # Split key into shares
        nr_shares = len(self._peer_hubs)
        shares = key.split_into_shares(nr_shares, _MIN_NR_SHARES)
        # Allocate encryption and authentication keys for each share
        for peer_hub, share in zip(self._peer_hubs, shares):
            share.allocate_encryption_and_authentication_keys_from_pool(peer_hub.pool)
        # TODO: Error handling. If there was an issue allocating any one of the encryption or
        #       authentication keys, deallocate all of the ones that were allocated, and return
        #       and error to the caller.
        # Encrypt and sign each share
        for share in shares:
            share.encrypt()
            share.sign()
        # POST the key shares to the peer hubs
        for peer_hub, share in zip(self._peer_hubs, shares):
            await peer_hub.post_share(share)
        # Delete folly consumed blocks from all pools
        for peer_hub in self._peer_hubs:
            peer_hub.delete_fully_consumed_blocks()

    async def gather_key_from_peer_hubs(self, key_uuid: UUID) -> Key:
        """
        Gather key shares from the peer hubs, and reconstruct the key out of (a subset of)
        the key shares.
        """
        # Attempt to get a key share from every peer hub.
        shares = []
        for peer_hub in self._peer_hubs:
            # TODO The client should allocated the allocations for the encryption key and the
            #      signature key; see fundamental problem in file TODO
            # TODO: Handle exception. If an exception occurs, we just skip the peer hub, and move
            #       on to the next one. We just need K out of N shares to reconstruct the key.
            share = await peer_hub.get_share(key_uuid)
            share.verify_signature()
            share.decrypt()
            shares.append(share)
            print(f"{share=}")  ### DEBUG

        # TODO: Check if we have enough shares
        # TODO: Reconstruct the key using Shamir secret sharing algorithm
        # Reconstruct the key from the shares
        shamir_input = [(share.share_index, share.value) for share in shares]
        print(f"{shamir_input=}")  ### DEBUG
        key_value = reconstruct_binary_secret_from_shares(shamir_input)
        print(f"{key_value=}")  ### DEBUG
        key = Key(key_uuid, key_value)
        print(f"Reconstructed key: {key}")  ### DEBUG
        return key
