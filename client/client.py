"""
A DSKE client, or just client for short.
"""

import asyncio
from typing import Any, List, Tuple
from uuid import UUID
from fastapi import status
from common import exceptions
from common import shamir
from common import utils
from common.logging import LOGGER
from common.user_key import UserKey
from common.utils import key_id_str_to_uuid
from .peer_hub import PeerHub


class Client:
    """
    A DSKE client, or just client for short.
    """

    _MIN_KEY_SIZE_IN_BITS = 32  # Shamir secret sharing needs at least 4 bytes.
    _MAX_KEY_SIZE_IN_BITS = 16_777_216  # Arbitrary large value
    _DEFAULT_KEY_SIZE_IN_BITS = 128
    _MAX_STORED_KEY_COUNT = 1_000  # Arbitrary large value
    _MAX_KEYS_PER_REQUEST = 1  # We don't support the number parameter for Get Key calls

    name: str
    encryptor_names: list[str]
    peer_hubs: list[PeerHub]

    def __init__(
        self,
        name: str,
        start_request_psrd_threshold: int,
        stop_request_psrd_threshold: int,
        get_psrd_block_size: int,
        min_nr_shares: int,
        encryptor_names: list[str],
        peer_hub_urls: list[str],
    ):
        self.name = name
        self.start_request_psrd_threshold = start_request_psrd_threshold
        self.stop_request_psrd_threshold = stop_request_psrd_threshold
        self.get_psrd_block_size = get_psrd_block_size
        self.min_nr_shares = min_nr_shares
        self.encryptor_names = encryptor_names
        self.peer_hubs = []
        for peer_hub_url in peer_hub_urls:
            peer_hub = PeerHub(self, peer_hub_url)
            self.peer_hubs.append(peer_hub)

    def to_mgmt(self):
        """
        Get the management status.
        """
        peer_hubs_status = [peer_hub.to_mgmt() for peer_hub in self.peer_hubs]
        return {
            "name": self.name,
            "start_request_psrd_threshold": self.start_request_psrd_threshold,
            "stop_request_psrd_threshold": self.stop_request_psrd_threshold,
            "get_psrd_block_size": self.get_psrd_block_size,
            "encryptor_names": self.encryptor_names,
            "peer_hubs": peer_hubs_status,
        }

    async def etsi_status(self, master_sae_id: str, slave_sae_id: str):
        """
        ETSI QKD 014 V1.1.1 Status API.
        """
        # Given a slave SAE ID, we have no easy way to know the target KME ID. This would
        # either require each KME (client) knowing the full topology or require each KME
        # known which QKD links exist. The current implementation does not require pre-configuration
        # of QKD links. Instead the master KME accepts every key request for any slave SAE ID.
        # The master KME doesn't know or care who the target KME is - it just generates a key,
        # splits it into shares, and scatters the shares to the peer hubs. The target KME, whoever
        # it is, will later gather the shares from the peer hubs. For that reason, we currently
        # return an empty string as the target KME ID.
        #
        # Similarly, we don't really have a concept of "stored keys" in this implementation.
        # How many keys can be "gotten" depends on many factors, including the PSRD pool sizes
        # at the source KME, each of the hubs, and the target KME (which we don't even know who
        # it is). For that reason, we return an arbitrary number as the stored key count.
        #
        return {
            "source_kme_id": self.name,
            "target_kme_id": "",  # See comment above
            "master_sae_id": master_sae_id,
            "slave_sae_id": slave_sae_id,
            "key_size": self._DEFAULT_KEY_SIZE_IN_BITS,
            "stored_key_count": 100,  # See comment above
            "max_key_count": self._MAX_STORED_KEY_COUNT,
            "max_key_per_request": self._MAX_KEYS_PER_REQUEST,
            "max_key_size": self._MAX_KEY_SIZE_IN_BITS,
            "min_key_size": self._MIN_KEY_SIZE_IN_BITS,
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
        if size is None:
            size = self._DEFAULT_KEY_SIZE_IN_BITS
        if size % 8 != 0:
            raise exceptions.KeySizeIsNotMultipleOfEightBitsError(size)
        if size < self._MIN_KEY_SIZE_IN_BITS or size > self._MAX_KEY_SIZE_IN_BITS:
            raise exceptions.KeySizeOutOfRangeError(
                size, self._MIN_KEY_SIZE_IN_BITS, self._MAX_KEY_SIZE_IN_BITS
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
        self, master_sae_id: str, slave_sae_id: str, key_id_str: str
    ):
        """
        ETSI QKD 014 V1.1.1 Get key with key IDs API.
        """
        key_id = key_id_str_to_uuid(key_id_str)
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
        for peer_hub in self.peer_hubs:
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
        nr_shares = len(self.peer_hubs)
        shares = key.split_into_shares(
            master_sae_id, slave_sae_id, nr_shares, self.min_nr_shares
        )
        assert len(shares) == nr_shares
        coroutines = [
            peer_hub.post_share(master_sae_id, slave_sae_id, share)
            for peer_hub, share in zip(self.peer_hubs, shares)
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
        if nr_shares_successfully_scattered < self.min_nr_shares:
            causes, status_code = self.summarize_failure(results)
            raise exceptions.CouldNotScatterEnoughSharesError(
                key.key_id,
                nr_shares_successfully_scattered,
                self.min_nr_shares,
                status_code,
                causes,
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
        nr_shares_attempted_to_gather = len(self.peer_hubs)
        coroutines = [
            peer_hub.get_share(master_sae_id, slave_sae_id, key_id)
            for peer_hub in self.peer_hubs
        ]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        shares = [result for result in results if not isinstance(result, Exception)]
        nr_shares_successfully_gathered = len(shares)
        LOGGER.info(
            f"Successfully gathered {nr_shares_successfully_gathered} shares "
            f"out of {nr_shares_attempted_to_gather} attempted "
            f"for key ID {key_id}"
        )
        if nr_shares_successfully_gathered < self.min_nr_shares:
            causes, status_code = self.summarize_failure(results)
            raise exceptions.CouldNotGatherEnoughSharesError(
                key_id,
                nr_shares_successfully_gathered,
                self.min_nr_shares,
                status_code,
                causes,
            )
        shamir_input = [(share.share_index, share.value) for share in shares]
        try:
            key_value = shamir.reconstruct_binary_secret_from_shares(
                self.min_nr_shares, shamir_input
            )
        except ValueError as exc:
            raise exceptions.ShamirReconstructError(key_id, str(exc)) from exc
        key = UserKey(key_id, key_value)
        return key

    @staticmethod
    def summarize_failure(hub_results: List[Any]) -> Tuple[List[str], int]:
        """
        Map multiple peer hub failures to a single summary ETSI failure.
        - A list of cause strings (included in the details of the ETSI exception)
        - The status code to be used in the ETSI exception, the worst of the peer status codes.
        """
        status_code = None
        causes = []
        for hub_result in hub_results:
            if isinstance(hub_result, Exception):
                causes.append(str(hub_result))
            if isinstance(hub_result, exceptions.DSKEException):
                if status_code is None or hub_result.status_code > status_code:
                    status_code = hub_result.status_code
        if status_code is None:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return (causes, status_code)
