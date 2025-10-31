"""
The key that is used to encrypt key shares in DSKE in-band protocol messages.
"""

from .allocation import Allocation
from .pool import Pool


class EncryptionKey:
    """
    The key that is used to encrypt key shares in DSKE in-band protocol messages.
    """

    def __init__(self, allocation: Allocation):
        """
        Should only be called from class methods from_xxx.
        """
        self._allocation = allocation

    @property
    def allocation(self) -> Allocation:
        """
        Get the allocation that holds the encryption key.
        """
        return self._allocation

    @classmethod
    def from_pool(cls, pool: Pool, key_size: int):
        """
        Allocate a new EncryptionKey from the given pool.
        """
        allocation = pool.allocate(key_size, "share-encryption-key")
        return EncryptionKey(allocation)

    @classmethod
    def from_allocation(cls, allocation):
        """
        Create an EncryptionKey from an existing allocation that was received from the peer.
        """
        return EncryptionKey(allocation)

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data and return the encrypted data.
        """
        encryption_key = self._allocation.data
        assert len(encryption_key) == len(data)
        encrypted_byte_list = [
            data_byte ^ encryption_key_byte
            for data_byte, encryption_key_byte in zip(data, encryption_key)
        ]
        encrypted_value = bytes(encrypted_byte_list)
        return encrypted_value

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt encrypted data and return the decrypted data.
        """
        # Since we do XOR encryption, encryption and decryption are the same operation.
        return self.encrypt(encrypted_data)
