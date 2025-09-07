"""
The internal keys that are used to encrypt user-key shares and to authenticate DSKE protocol
messages.

These internal keys must not be confused with the keys which are delivered to users (see class
UserKey).

An InternalKeys objects contains three different internal keys:
- The encryption key that is used to encrypt and decrypt user shares.
- The authentication key that is used to authenticate client->hub request messages.
- The authentication key that is used to authenticate hub->client response messages.

We use separate keys for encryption and authentication (see
https://crypto.stackexchange.com/questions/12090/using-the-same-rsa-keypair-to-sign-and-encrypt).
We do use the same authentication key for the request message and the response message (if that
turns out to be an issue, we can easily change that to use different keys).

Each of these three internal keys is allocated from Pre-Shared Random Data (PSRD).

Internal keys MUST always be allocated on the client side and never on the hub side to
avoid race conditions on who (client or hub) allocates which bytes in the pool.

For POST key-share
- The client
  - Allocates and consumes the encryption key, and uses it to encrypt the share.
  - Allocates and consumes the authentication key, and uses it to sign the request.
  - Sends the encryption and the authentication key allocations to the hub (internal_keys).
- The hub:
  - Uses the received encryption key allocation to decrypt the received share.
  - Uses the received authentication key allocation to validate the request and sign the response.

For GET key-share:
- The client
  - Allocates and but does not consume the encryption key.
  - Allocates and consumes the authentication key, and uses it to sign the request and to validate
    the response.
  - Sends the encryption and the authentication key allocations to the hub (internal_keys).
- The hub:
  - Uses the received encryption key allocation to encrypt the sent share.
  - Uses the received authentication key allocation to validate the request and sign the response.
"""

# TODO: Add a seq_nr field to the API for replay attack prevention


from .pool import Pool


class InternalKeys:
    """
    The set of internal keys used within the DSKE protocol to encrypt user-key shares and to
    authenticate (sign) DSKE protocol messages.
    """

    _ENCRYPTION_KEY_SIZE = 64  # bytes
    _AUTHENTICATION_KEY_SIZE = 32  # bytes

    def __init__(self):
        self._encryption_key_allocation = None
        self._authentication_key_allocation = None

    @property
    def encryption_key_allocation(self):
        """
        Get the encryption key allocation.
        """
        return self._encryption_key_allocation

    @property
    def authentication_key_allocation(self):
        """
        Get the authentication key allocation.
        """
        return self._authentication_key_allocation

    def allocate(self, pool: Pool):
        """
        Allocate (but don't yet consume) the internal keys.
        """
        assert self._encryption_key_allocation is None
        assert self._authentication_key_allocation is None
        self._encryption_key_allocation = pool.allocate(self._ENCRYPTION_KEY_SIZE)
        self._authentication_key_allocation = pool.allocate(
            self._AUTHENTICATION_KEY_SIZE
        )

    def compute_authentication_signature(self) -> str:
        """
        Compute the authentication signature for a message, using the given authentication key
        allocation.
        """
        assert self._authentication_key_allocation is not None
        self._authentication_key_allocation.consume()
        _authentication_key = self._authentication_key_allocation.value
        return "foobar"  # TODO
