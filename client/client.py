"""
A DSKE client, or just client for short.
"""

import asyncio
from uuid import UUID
from common import exceptions
from common import shamir
from common import utils
from common.logging import LOGGER
from common.user_key import UserKey
from .peer_hub import PeerHub

# TODO: Make this configurable
# TODO: The Shamir code also has a max (is that really needed?)
_MIN_NR_SHARES = 3  # The minimum number of key shares required to reconstruct the key.


class Client:
    """
    A DSKE client, or just client for short.
    """

    _min_key_size_in_bits = 32  # Shamir secret sharing needs at least 4 bytes.
    _max_key_size_in_bits = 16_777_216  # TODO: Pick a value (make it a power of 2)
    _default_key_size_in_bits = 128
    _max_stored_key_count = 1000  # TODO: What is a sensible value?
    _max_keys_per_request = 1  # TODO: Allow more than one

    _name: str
    _encryptor_names: list[str]
    _peer_hubs: list[PeerHub]

    def __init__(self, name: str, encryptor_names: list[str], peer_hub_urls: list[str]):
        self._name = name
        self._encryptor_names = encryptor_names
        self._peer_hubs = []
        for peer_hub_url in peer_hub_urls:
            peer_hub = PeerHub(self, peer_hub_url)
            self._peer_hubs.append(peer_hub)

    @property
    def name(self):
        """
        Get the name.
        """
        return self._name

    @property
    def encryptor_names(self):
        """
        Get the encryptor names.
        """
        return self._encryptor_names

    def to_mgmt(self):
        """
        Get the management status.
        """
        peer_hubs_status = [peer_hub.to_mgmt() for peer_hub in self._peer_hubs]
        return {
            "name": self._name,
            "encryptor_names": self._encryptor_names,
            "peer_hubs": peer_hubs_status,
        }

    async def etsi_status(self, master_sae_id: str, slave_sae_id: str):
        """
        ETSI QKD 014 V1.1.1 Status API.
        """
        # See remark about ETSI QKD API in file TODO
        return {
            "source_kme_id": self._name,
            "target_kme_id": "TODO",  # TODO: Determine slave KME ID from slave SAE ID
            "master_sae_id": master_sae_id,
            "slave_sae_id": slave_sae_id,
            "key_size": self._default_key_size_in_bits,
            "stored_key_count": 25000,  # TODO
            "max_key_count": self._max_stored_key_count,
            "max_key_per_request": self._max_keys_per_request,
            "max_key_size": self._max_key_size_in_bits,
            "min_key_size": self._min_key_size_in_bits,
            "max_sae_id_count": 0,
        }

    async def etsi_get_key(
        self,
        master_sae_id: str,
        slave_sae_id: str,
        size: int | None = None,
    ):
        """
        ETSI QKD 014 V1.1.1 Get key API.
        """
        # TODO: Make sure that this client is actually the initiator
        # TODO: Use the Slave SAE ID?
        # TODO: Store the _slave_sae_id somewhere. It should be used to determine who is allowed
        #       to retrieve the key on the other side by calling Get Key with Key IDs.
        #       Perhaps also store the master_sae_id to keep track of who the initiator/master is.
        if size is None:
            size = self._default_key_size_in_bits
        if size % 8 != 0:
            raise exceptions.KeySizeIsNotMultipleOfEightBitsError(size)
        if size < self._min_key_size_in_bits or size > self._max_key_size_in_bits:
            raise exceptions.KeySizeOutOfRangeError(
                size, self._min_key_size_in_bits, self._max_key_size_in_bits
            )
        size_in_bytes = size // 8
        key = UserKey.create_random_key(size_in_bytes)
        await self.scatter_key_amongst_peer_hubs(master_sae_id, slave_sae_id, key)
        return {
            "keys": {
                "key_ID": key.key_id,
                "key": utils.bytes_to_str(key.value),
            }
        }

    async def etsi_get_key_with_key_ids(
        self, master_sae_id: str, slave_sae_id: str, key_id: str
    ):
        """
        ETSI QKD 014 V1.1.1 Get key with key IDs API.
        """
        try:
            key_id = UUID(key_id)
        except ValueError as exc:
            raise exceptions.InvalidKeyIDError(key_id) from exc
        key = await self.gather_key_from_peer_hubs(master_sae_id, slave_sae_id, key_id)
        return {
            "keys": [
                {
                    "key_ID": key.key_id,
                    "key": utils.bytes_to_str(key.value),
                }
            ]
        }

    def start_all_peer_hubs(self) -> None:
        """
        Start all peer hubs.
        """
        for peer_hub in self._peer_hubs:
            peer_hub.start_register_task()

    async def scatter_key_amongst_peer_hubs(
        self,
        master_sae_id: str,
        slave_sae_id: str,
        key: UserKey,
    ) -> None:
        """
        Split the key into key shares, and send each key share to a peer hub.
        """
        nr_shares = len(self._peer_hubs)
        shares = key.split_into_shares(
            master_sae_id, slave_sae_id, nr_shares, _MIN_NR_SHARES
        )
        assert len(shares) == nr_shares
        coroutines = [
            peer_hub.post_share(master_sae_id, slave_sae_id, share)
            for peer_hub, share in zip(self._peer_hubs, shares)
        ]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        success_results = [
            result for result in results if not isinstance(result, Exception)
        ]
        nr_shares_successfully_scattered = len(success_results)
        LOGGER.info(
            f"Successfully scattered {nr_shares_successfully_scattered} out of {nr_shares} shares "
            f"for key ID {key.key_id}"
        )
        if nr_shares_successfully_scattered < _MIN_NR_SHARES:
            causes = [
                str(result) for result in results if isinstance(result, Exception)
            ]
            raise exceptions.CouldNotScatterEnoughSharesError(
                key.key_id, nr_shares_successfully_scattered, _MIN_NR_SHARES, causes
            )

    async def gather_key_from_peer_hubs(
        self,
        master_sae_id: str,
        slave_sae_id: str,
        key_id: UUID,
    ) -> UserKey:
        """
        Gather key shares from the peer hubs, and reconstruct the key out of (a subset of)
        the key shares.
        """
        nr_shares_attempted_to_gather = len(self._peer_hubs)
        coroutines = [
            peer_hub.get_share(master_sae_id, slave_sae_id, key_id)
            for peer_hub in self._peer_hubs
        ]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        shares = [result for result in results if not isinstance(result, Exception)]
        nr_shares_successfully_gathered = len(shares)
        LOGGER.info(
            f"Successfully gathered {nr_shares_successfully_gathered} shares "
            f"out of {nr_shares_attempted_to_gather} attempted "
            f"for key ID {key_id}"
        )
        if nr_shares_successfully_gathered < _MIN_NR_SHARES:
            causes = [
                str(result) for result in results if isinstance(result, Exception)
            ]
            raise exceptions.CouldNotGatherEnoughSharesError(
                key_id, nr_shares_successfully_gathered, _MIN_NR_SHARES, causes
            )
        shamir_input = [(share.share_index, share.value) for share in shares]
        try:
            key_value = shamir.reconstruct_binary_secret_from_shares(
                _MIN_NR_SHARES, shamir_input
            )
        except ValueError as exc:
            raise exceptions.ShamirReconstructError(key_id, str(exc)) from exc
        key = UserKey(key_id, key_value)
        return key
