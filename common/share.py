"""
A share of a key.
"""

from uuid import UUID
from .exceptions import WrongMasterSAEIDError, WrongSlaveSAEIDError
from .utils import bytes_to_str


class Share:
    """
    A share of a user key. A user key is split up into multiple (`nr_shares`) `shares. The user key
    can be reconstructed from a subset (`min_nr_shares`) of these shares.
    """

    _master_sae_id: str
    _slave_sae_id: str
    _user_key_id: UUID
    _share_index: int
    _value: bytes

    def __init__(
        self,
        master_sae_id: str,
        slave_sae_id: str,
        user_key_id: UUID,
        share_index: int,
        value: bytes | None = None,
    ):
        self._master_sae_id = master_sae_id
        self._slave_sae_id = slave_sae_id
        self._user_key_id = user_key_id
        self._share_index = share_index
        self._value = value

    @property
    def master_sae_id(self) -> str:
        """
        Get the master SAE ID.
        """
        return self._master_sae_id

    @property
    def slave_sae_id(self) -> str:
        """
        Get the slave SAE ID.
        """
        return self._slave_sae_id

    @property
    def user_key_id(self) -> UUID:
        """
        Get the user key UUID.
        """
        return self._user_key_id

    @property
    def share_index(self) -> int:
        """
        Get the share index.
        """
        return self._share_index

    @property
    def value(self) -> bytes:
        """
        Get the (unencrypted) share value.
        """
        return self._value

    @property
    def size(self) -> int:
        """
        Get the share size in bytes. The size is the same for the unencrypted and encrypted value.
        """
        return len(self._value)

    @staticmethod
    def share_size_for_key_size(key_size) -> int:
        """
        Get the size of each share for a key of the given size in bytes.
        """
        return key_size

    def __repr__(self) -> str:
        """
        Get a string representation.
        """
        return str(self.to_mgmt())

    def to_mgmt(self):
        """
        Get the management status.
        """
        return {
            "master_sae_id": self._master_sae_id,
            "slave_sae_id": self._slave_sae_id,
            "key_id": str(self._user_key_id),
            "share_index": self._share_index,
            "value": bytes_to_str(self._value, truncate=True),
        }

    def check_master_sae(self, master_sae_id: str):
        """
        Check if the given master SAE ID matches the stored master SAE ID.
        Raise an exception if not.
        """
        if self.master_sae_id != master_sae_id:
            key_id_str = str(self.user_key_id)
            raise WrongMasterSAEIDError(master_sae_id, self.master_sae_id, key_id_str)

    def check_slave_sae(self, slave_sae_id: str):
        """
        Check if the given slave SAE ID matches the stored slave SAE ID.
        Raise an exception if not.
        """
        if self.slave_sae_id != slave_sae_id:
            key_id_str = str(self.user_key_id)
            raise WrongSlaveSAEIDError(slave_sae_id, self.slave_sae_id, key_id_str)
