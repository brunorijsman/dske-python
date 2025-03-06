"""
Pre-Shared Random Data (PSRD) block.
"""

from uuid import UUID, uuid4
import os
from pydantic import PositiveInt


class PSRDBlock:
    """
    A block of Pre-Shared Random Data (PSRD).
    """
    _uuid: UUID
    _original_size: int
    _remaining_size: int
    _data: bytes

    def __init__(self, uuid: UUID, data: bytes):
        self._uuid = uuid
        self._original_size = len(data)
        self._remaining_size = self._original_size
        self._data = data

    @classmethod
    def create_random_psrd_block(cls, size: PositiveInt):
        """
        Create a random PSRD block, containing `size` random bytes.
        """
        uuid = uuid4()
        data = os.urandom(size)
        return PSRDBlock(uuid, data)

    @property
    def remaining_size(self):
        """
        The remaining number of bytes in the PSRD block.
        """
        return self._remaining_size
