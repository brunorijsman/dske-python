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
    _original_size: int  # In bytes
    _remaining_size: int  # In bytes
    _data: bytes
    _allocated: bitarray

    def __init__(self, uuid: UUID, data: bytes):
        self._uuid = uuid
        # TODO: Do we need original size? Isn't this just the size of the data field?
        self._original_size = len(data)
        self._remaining_size = self._original_size
        self._data = data
        self._allocated = bitarray(self._original_size)

    @property
    def uuid(self):
        """
        The UUID of the PSRD block.
        """
        return self._uuid

    @property
    def remaining_size(self):
        """
        The remaining number of bytes that have not yet been consumed.
        """
        return self._remaining_size

    def to_management_json(self):
        """
        Get a JSON representation of the PSRD block, for the purpose of sending it to the management
        interface.
        """
        return {
            "uuid": str(self._uuid),
            "original_size": self._original_size,
            "remaining_size": self._remaining_size,
            "data": common.bytes_to_str(self._data, truncate=True),
        }

    def to_protocol_json(self):
        """
        Convert to JSON representation as used in the DSKE protocol.
        """
        # Blocks should only be sent over protocol message before any bytes are allocated.
        assert self._remaining_size == self._original_size
        return {
            "uuid": str(self._uuid),
            "data": common.bytes_to_str(self._data),
        }

    @classmethod
    def from_protocol_json(cls, json: dict):
        """
        Convert from JSON representation as used in the DSKE protocol.
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
            found_end = self._original_size
        found_size = found_end - found_start
        if found_size > desired_size:
            found_end = found_start + desired_size
            found_size = desired_size
        self._allocated[found_start:found_end] = True
        self._remaining_size -= found_size
        return Fragment(self, found_start, found_size)

    def deallocate_fragment(self, fragment: Fragment):
        """
        Deallocate a PSRD fragment from the block.
        """
        # Once a fragment is consumed, it cannot be deallocated anymore. This is intended for
        # returning already allocated fragments if cannot gather enough fragments to form an
        # Allocation object.
        end_byte = fragment.start_byte + fragment.size
        self._allocated[fragment.start_byte : end_byte] = False
        self._remaining_size += fragment.size
