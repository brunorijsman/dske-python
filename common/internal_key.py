"""
The internal keys that are used to encrypt user-key shares that are present in certain in-band DSKE
protocol messages.

The share encryption keys must not be confused with the keys which are delivered to users
(see class UserKey).

We use separate keys for encryption (class InternalKey) and message authentication
(class AuthenticationKey).
See also
https://crypto.stackexchange.com/questions/12090/using-the-same-rsa-keypair-to-sign-and-encrypt.

TODO: Move all this explanation to the developer documentation

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

import hashlib
import hmac
import sys
from common.utils import bytes_to_str, str_to_bytes
from .allocation import Allocation
from .pool import Pool


# TODO: Split this up into SigningKey and EncryptionKey after all.


class InternalKey:
    """
    A key that is used internally within the DSKE protocol to encrypt the user-key shares or to
    sign messages.
    """

    SIGNING_KEY_SIZE = 32  # bytes

    SIGNING_KEY_HEADER_NAME = "DSKE-Signing-Key"

    # TODO: Introduce a Signature class
    SIGNATURE_HEADER_NAME = "DSKE-Signature"

    def __init__(self, allocation: Allocation):
        """
        Don't call the constructor directly, use from... methods instead.
        """
        self._allocation = allocation
        self._allocation.consume()

    @classmethod
    def from_pool(cls, pool: Pool, key_size: int):
        """
        Allocate a new InternalKey from the given pool.
        """
        allocation = pool.allocate(key_size)
        return InternalKey(allocation)

    @classmethod
    def from_allocation(cls, allocation):
        """
        Create an InternalKey from an existing allocation that was received from the peer.
        """
        allocation.mark_allocated()
        return InternalKey(allocation)

    @property
    def allocation(self):
        """
        Get the allocation.
        """
        return self._allocation

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data and return the encrypted data.
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
        Decrypt encrypted data and return the decrypted data.
        """
        # Since we do XOR encryption, encryption and decryption are the same operation.
        return self.encrypt(encrypted_data)

    def sign(self, data: bytes) -> bytes:
        """
        Sign data and return the signature.
        """
        signing_key = self._allocation.value
        h = hmac.new(signing_key, data, hashlib.sha256)
        signature_bin = h.digest()
        return signature_bin

    def make_authentication_header(
        self,
        params: bytes | None,
        content: bytes | None,
    ) -> str:
        """
        Create the value for the DSKE-Signature header for a request with the given query
        parameters and content.
        TODO: Add a nonce to prevent replay attacks.
        TODO: Should we also sign the URL path?
        """
        assert params is not None or content is not None
        signed_data = b""
        if params is not None:
            signed_data += params
        if content is not None:
            signed_data += content
        allocation_str = self._allocation.to_param_str()
        signing_key_bin = self._allocation.value
        header_value = self.make_authentication_header_from_allocation_str(
            allocation_str, signing_key_bin, signed_data
        )
        return header_value

    # TODO: Not a static method but stand-alone method. Ditto for next.
    @staticmethod
    def make_authentication_header_from_allocation_str(
        allocation_str: str, signing_key_bin: bytes, signed_data: bytes
    ) -> str:
        """
        Create the value for the DSKE-Signature header from the given allocation string and
        signing key.
        """
        h = hmac.new(signing_key_bin, signed_data, hashlib.sha256)
        signature_bin = h.digest()
        signature_str = bytes_to_str(signature_bin)
        header_value = f"{allocation_str};{signature_str}"
        return header_value

    @staticmethod
    def check_authentication_header(
        pool: Pool,
        params: bytes | None,
        content: bytes | None,
        authentication_header: str,
    ) -> bool:
        """
        Check the authentication header for a request with the given query parameters and content.
        """
        splitted = authentication_header.split(";")
        if len(splitted) != 2:
            print("Authentication mismatch", file=sys.stderr)  # TODO $$$
            return False
        allocation_str = splitted[0]
        signature_str = splitted[1]
        allocation = Allocation.from_param_str(allocation_str, pool)
        authentication_key = InternalKey.from_allocation(allocation)
        signature_bin = str_to_bytes(signature_str)
        assert params is not None or content is not None
        signed_data = b""
        if params is not None:
            signed_data += params
        if content is not None:
            signed_data += content
        if authentication_key.sign(signed_data) == signature_bin:
            print("Authentication succeeded", file=sys.stderr)  # TODO $$$
            return True
        allocation.deallocate()
        print("Authentication mismatch", file=sys.stderr)  # TODO $$$
        return False
