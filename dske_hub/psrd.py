"""
Pre-Shared Random Data (PSRD) block.
"""

from uuid import UUID, uuid4
from os import urandom
from pydantic import PositiveInt


class PSRD:
    """
    Pre-Shared Random Data (PSRD).
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
    def create_random_psrd(cls, size: PositiveInt):
        """
        Create a PSRD, containing `size` random bytes.
        """
        uuid = uuid4()
        data = urandom(size)
        return PSRD(uuid, data)

    @property
    def uuid(self):
        """
        The UUID of the PSRD.
        """
        return self._uuid

    @property
    def remaining_size(self):
        """
        The remaining number of bytes in the PSRD.
        """
        return self._remaining_size
