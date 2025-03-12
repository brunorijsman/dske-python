"""
A Pre-Shared Random Data (PSRD) block.
"""

from uuid import UUID, uuid4
import os

from bitarray import bitarray
from pydantic import PositiveInt

import common

from .fragment import Fragment


class Block:
    """
    A Pre-Shared Random Data (PSRD) block.
    """

    _uuid: UUID
    _size: int  # In bytes
    _data: bytes
    _allocated: bitarray
    _consumed: bitarray

    def __init__(self, uuid: UUID, data: bytes):
        self._uuid = uuid
        self._size = len(data)
        # TODO: Use consistent naming: data or value
        self._data = data
        self._allocated = bitarray(self._size)
        self._consumed = bitarray(self._size)

    @property
    def uuid(self):
        """
        The UUID of the PSRD block.
        """
        return self._uuid

    def to_mgmt_dict(self):
        """
        Get a JSON representation of the PSRD block, for the purpose of sending it to the management
        interface.
        """
        return {
            "uuid": str(self._uuid),
            "data": common.bytes_to_str(self._data, truncate=True),
        }

    def to_api_dict(self):
        """
        Convert to JSON representation as used in the DSKE API.
        """
        return {
            "uuid": str(self._uuid),
            "data": common.bytes_to_str(self._data),
        }

    @classmethod
    def from_api_dict(cls, json: dict):
        """
        Convert from JSON representation as used in the DSKE API.
        """
        # TODO: Error handling
        return Block(
            UUID(json["uuid"]),
            common.str_to_bytes(json["data"]),
        )

    @classmethod
    def create_random_psrd_block(cls, size: PositiveInt):
        """
        Create a PSRD block, containing `size` random bytes.
        """
        uuid = uuid4()
        data = os.urandom(size)
        return Block(uuid, data)

    def allocate_fragment(self, desired_size: PositiveInt) -> Fragment | None:
        """
        Allocate a PSRD fragment from the block. We try to allocate `desired_size` bytes from the
        block, but we accept a smaller fragment if there is not enough data left in the block. We a
        fragment for the first unallocated set of bytes in the block (i.e. we don't try to search
        further for a larger gap).
        """
        try:
            found_start = self._allocated.index(False)
        except ValueError:
            return None
        try:
            found_end = self._allocated.index(True, found_start)
        except ValueError:
            found_end = self._size
        found_size = found_end - found_start
        if found_size > desired_size:
            found_end = found_start + desired_size
            found_size = desired_size
        self._allocated[found_start:found_end] = True
        return Fragment(self, found_start, found_size)

    def deallocate_fragment(self, fragment: Fragment):
        """
        Deallocate a PSRD fragment from the block.
        """
        end_byte = fragment.start_byte + fragment.size
        self._allocated[fragment.start_byte : end_byte] = False

    def consume_fragment(self, fragment: Fragment):
        """
        Consume a PSRD fragment from the block.
        """
        start = fragment.start_byte
        end = start + fragment.size
        assert self._allocated[start:end].all()
        assert not self._consumed[start:end].any()
        self._consumed[start:end] = True
        consumed_data = self._data[start:end]
        # Zero out allocated bytes in block
        self._data = self._data[:start] + b"\x00" * fragment.size + self._data[end:]
        return consumed_data

    def is_fully_consumed(self):
        """
        Check if all bytes in the block have been consumed.
        """
        return self._consumed.all()
