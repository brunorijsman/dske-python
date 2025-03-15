"""
A Pre-Shared Random Data (PSRD) block.
"""

from uuid import UUID, uuid4
import os
import pydantic
from bitarray import bitarray
from pydantic import PositiveInt
from .common import bytes_to_str, str_to_bytes
from .fragment import Fragment


class APIBlock(pydantic.BaseModel):
    """
    Representation of a PSRD block as used in API calls.
    """

    block_uuid: str
    data: str


class Block:
    """
    A Pre-Shared Random Data (PSRD) block.
    """

    _block_uuid: UUID
    _size: int  # In bytes
    _data: bytes
    _allocated: bitarray
    _consumed: bitarray

    def __init__(self, block_uuid: UUID, data: bytes):
        self._block_uuid = block_uuid
        self._size = len(data)
        # TODO: Use consistent naming: data or value
        self._data = data
        self._allocated = bitarray(self._size)
        self._consumed = bitarray(self._size)

    @property
    def uuid(self):
        """
        The UUID of the block.
        """
        return self._block_uuid

    def to_mgmt(self):
        """
        Get the management status.
        """
        return {
            "uuid": str(self._block_uuid),
            "size": self._size,
            "data": bytes_to_str(self._data, truncate=True),
            "allocated": self._allocated.count(),
            "consumed": self._consumed.count(),
        }

    @classmethod
    def create_random_block(cls, size: PositiveInt):
        """
        Create a block, containing `size` random bytes.
        """
        uuid = uuid4()
        data = os.urandom(size)
        return Block(uuid, data)

    def allocate_fragment(self, desired_size: PositiveInt) -> Fragment | None:
        """
        Allocate a fragment from the block. We try to allocate `desired_size` bytes from the
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
        Deallocate a fragment from the block.
        """
        end_byte = fragment.start_byte + fragment.size
        self._allocated[fragment.start_byte : end_byte] = False

    def mark_fragment_allocated(self, fragment: Fragment):
        """
        Mark the bits in the block corresponding to the fragment as allocated.
        """
        assert fragment.start_byte is not None
        assert fragment.size is not None
        start = fragment.start_byte
        end = start + fragment.size
        assert not self._allocated[start:end].any()
        self._allocated[start:end] = True

    def consume_fragment(self, fragment: Fragment):
        """
        Consume a fragment from the block.
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

    @classmethod
    def from_api(cls, api_block: APIBlock) -> "Block":
        """
        Create a Block from an APIBlock.
        """
        # TODO: Error handling
        return Block(UUID(api_block.block_uuid), str_to_bytes(api_block.data))

    def to_api(self) -> APIBlock:
        """
        Create an APIBLock from a Block.
        """
        return APIBlock(
            block_uuid=str(self._block_uuid),
            data=bytes_to_str(self._data),
        )
