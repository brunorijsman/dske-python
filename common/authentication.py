"""
DSKE authentication, using signatures computed using a key that is allocated from Pre-Shared Random
data (PSRD).
"""

from .pool import Pool


_AUTHENTICATION_KEY_SIZE = 32  # bytes


def compute_signature(_pool: Pool) -> str:
    """
    Compute an authentication signature using a key allocated from the given pool.
    """
    # TODO: This causes the get-key-pair to fail because of
    # key_allocation = pool.allocate(_AUTHENTICATION_KEY_SIZE)
    # key_allocation.consume()
    # _key_value = key_allocation.value
    # TODO: Need to introduce the concept of PSRD ownership before we can continue.
    # TODO: Compute real signature
    return "foobar"  # TODO
