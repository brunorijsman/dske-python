"""
A Pre-Shared Random Data (PSRD) block.
"""

from uuid import UUID, uuid4
import os

from bitarray import bitarray
from pydantic import PositiveInt

import common

from .allocation import Allocation
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
        Get a JSON representation of the PSRD block, for the purpose of sending it in a protocol
        message.
        """
        # Blocks should only be sent over protocol message before any bytes are allocated.
        assert self._remaining_size == self._original_size
        return {
            "uuid": str(self._uuid),
            "data": common.bytes_to_str(self._data),
        }

    @classmethod
    def from_protocol_json(cls, json):
        """
        Create a PSRD block from the JSON representation.
        """
        # TODO: Error handling
        uuid = json["uuid"]
        data = common.str_to_bytes(json["data"])
        return Block(uuid, data)

    @classmethod
    def create_random_psrd_block(cls, size: PositiveInt):
        """
        Create a PSRD block, containing `size` random bytes.
        """
        uuid = uuid4()
        data = os.urandom(size)
        return Block(uuid, data)

    def allocate_psrd_fragment(self, desired_size: PositiveInt) -> Fragment | None:
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

    def deallocate_psrd_fragment(self, fragment: Fragment):
        """
        Deallocate a PSRD fragment from the block.
        """
        end_byte = fragment.start_byte + fragment.size
        self._allocated[fragment.start_byte : end_byte] = False
        self._remaining_size += fragment

    def allocate_psrd_allocation(self, desired_size: PositiveInt) -> Allocation | None:
        """
        Allocate a PSRD allocation from the block. An allocation consists of one or more fragments.
        This either returns an allocation for the full `desired_size` or None if there is not enough
        unallocated data left in the block.
        """
        fragments = []
        remaining_size = desired_size
        while remaining_size > 0:
            fragment = self.allocate_psrd_fragment(remaining_size)
            if fragment is None:
                break
            fragments.append(fragment)
            remaining_size -= fragment.size
        if remaining_size > 0:
            # We didn't allocate the full desired size, deallocate the fragments we did allocate.
            for fragment in fragments:
                self.deallocate_psrd_fragment(fragment)
            return None
        return Allocation(fragments)
