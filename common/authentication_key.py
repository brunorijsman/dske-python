"""
The internal keys that are used to authenticate DSKE protocol messages.

The message authentication keys must not be confused with the keys which are delivered to users
(see class UserKey).

We use separate keys for encryption (class EncryptionKey) and message authentication
(class AuthenticationKey).
See also
https://crypto.stackexchange.com/questions/12090/using-the-same-rsa-keypair-to-sign-and-encrypt.
We do use the same authentication key for the request message and the response message (if that
turns out to be an issue, we can easily change that to use different keys).

The MessageAuthentication keys are allocated from Pre-Shared Random Data (PSRD).

MessageAuthentication keys MUST always be allocated on the client side and never on the hub side to
avoid race conditions with respect to who (client or hub) allocates which bytes in the pool.

For all in-band DSKE protocol messages (i.e. HTTP requests and responses):
- The client
  - Allocates and consumes the authentication key for the request/response pair from the
    client pool.
  - Uses the authentication key to sign the request.
  - Sends a DSKE-Authentication header in the request to the hub, containing:
    - The authentication key allocation
    - The signature of the request
  - Uses the authentication key to validate the response signature.
- The hub:
  - Receives the DSKE-Authentication header in the request from the client.
  - Allocates and consumes the authentication key for the request/response pair from the hub pool.
  - Uses the received authentication key allocation to validate the request signature.
  - Uses the authentication key to sign the response.
"""

# TODO: Add a seq_nr field to the API for replay attack prevention


import sys
from .pool import Pool


class AuthenticationKey:
    """
    A key that is used internally within the DSKE protocol to authenticated (sign) in-band
    DSKE protocol messages.
    """

    _KEY_SIZE = 32  # bytes

    def __init__(self, pool: Pool):
        self._allocation = pool.allocate(self._KEY_SIZE)
        self._allocation.consume()

    @property
    def allocation(self):
        """
        Get the allocation.
        """
        return self._allocation

    def sign_message(self, message_params_str: str, message_body_str: str) -> str:
        """
        Compute the signature for a message.
        """
        print("Compute signature for message", file=sys.stderr)
        print(f"{message_params_str=}", file=sys.stderr)
        print(f"{message_body_str}", file=sys.stderr)
        # TODO: implement this for real
        return "foobar"

    def validate_message_signature(
        self, _message_params_str: str, _message_body_str: str, signature_str: str
    ) -> bool:
        """
        Validate the signature for a message.
        """
        # TODO: implement this for real
        return signature_str == "foobar"
