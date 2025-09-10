"""
The internal keys that are used to encrypt user-key shares that are present in certain in-band DSKE
protocol messages.

The share encryption keys must not be confused with the keys which are delivered to users
(see class UserKey).

We use separate keys for encryption (class EncryptionKey) and message authentication
(class AuthenticationKey).
See also
https://crypto.stackexchange.com/questions/12090/using-the-same-rsa-keypair-to-sign-and-encrypt.

The MessageAuthentication keys are allocated from Pre-Shared Random Data (PSRD).

MessageAuthentication keys MUST always be allocated on the client side and never on the hub side to
avoid race conditions with respect to who (client or hub) allocates which bytes in the pool.

For POST key-share
- The client
  - Allocates and consumes the share encryption key.
  - Uses the share encryption key to encrypt the share before it is sent to the hub.
  - Sends the share encryption key allocation to the hub as a JSON field in the request body.
- The hub:
  - Receives the share encryption key allocation from the client.
  - Allocates and consumes the share encryption key from its own pool (it should match the clients
    encryption key)
` - Uses the share encryption key to decrypt the received share.

For GET key-share
- The client
  - Allocates and consumes the share encryption key.
  - Sends the share encryption key allocation to the hub as a JSON field in the request body.
` - Uses the share encryption key to decrypt the received share received in the response from the
    hub.
- The hub:
  - Receives the share encryption key allocation from the client.
  - Allocates and consumes the share encryption key from its own pool (it should match the clients
    encryption key)
  - Uses the share encryption key to encrypt the share before it is sent to the client.
"""

from .allocation import Allocation
from .pool import Pool


class EncryptionKey:
    """
    A key that is used internally within the DSKE protocol to encrypt the user-key shares.
    """

    def __init__(self, allocation: Allocation):
        """
        Don't call the constructor directly, use from... methods instead.
        """
        self._allocation = allocation
        self._allocation.consume()

    @classmethod
    def from_pool(cls, pool: Pool, key_size: int):
        """
        Allocate a new EncryptionKey from the given pool.
        """
        allocation = pool.allocate(key_size)
        return EncryptionKey(allocation)

    @classmethod
    def from_allocation(cls, allocation):
        """
        Create an EncryptionKey from an existing allocation.
        """
        return EncryptionKey(allocation)

    @property
    def allocation(self):
        """
        Get the allocation.
        """
        return self._allocation

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data.
        """
        encryption_key = self._allocation.value
        assert len(encryption_key) == len(data)
        encrypted_byte_list = [
            data_byte ^ encryption_key_byte
            for data_byte, encryption_key_byte in zip(data, encryption_key)
        ]
        encrypted_value = bytes(encrypted_byte_list)
        return encrypted_value

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt encrypted data.
        """
        # Since we do XOR encryption, encryption and decryption are the same operation.
        return self.encrypt(encrypted_data)
