"""
A Pre-Shared Random Data (PSRD) key.
"""

from uuid import UUID, uuid4
from pydantic import PositiveInt


import psrd


class PSRDKey:
    """
    A Pre-Shared Random Data (PSRD) key. The key value is consumed from a PSRD pool. It is used to
    either encrypt or sign a user key share (UserKeyShare).
    """

    def __init__(self, psrd_key_uuid: UUID, allocation: psrd.Allocation):
        self._psrd_key_uuid = psrd_key_uuid
        self._allocation = allocation

    @classmethod
    def allocate_psrd_key(cls, pool: psrd.Pool, size: PositiveInt) -> "PSRDKey":
        """
        Allocate a PSRD key from a PSRD pool. The key value is only allocated; it is not consumed
        yet. This means that there is still the opportunity to deallocate th key and return it to
        the pool. This is needed when allocating a single PSRD key is part of some larger
        transaction that has to atomically either succeed or fail.
        """
        uuid = uuid4()
        allocation = pool.allocate_allocation(size)
        if allocation is None:
            # TODO: Better exception type (also fix catch side when it's changed)
            raise RuntimeError("Not enough PSRD available")
        return PSRDKey(uuid, allocation)
