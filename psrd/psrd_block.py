"""
A Pre-Shared Random Data (PSRD) block.
"""

from uuid import UUID, uuid4
from os import urandom
from pydantic import PositiveInt


class PSRDBlock:
    """
    A Pre-Shared Random Data (PSRD) block.
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

    @property
    def uuid(self):
        """
        The UUID of the PSRD block.
        """
        return self._uuid

    def json(self):
        """
        Get a JSON representation of the PSRD block.
        """
        return {
            "uuid": self._uuid,
            "original_size": self._original_size,
            "remaining_size": self._remaining_size,
        }

    @classmethod
    def create_random_psrd_block(cls, size: PositiveInt):
        """
        Create a PSRD block, containing `size` random bytes.
        """
        uuid = uuid4()
        data = urandom(size)
        return PSRDBlock(uuid, data)

    @property
    def remaining_size(self):
        """
        The remaining number of bytes that have not yet been consumed.
        """
        return self._remaining_size
