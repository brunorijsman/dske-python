"""
A Pre-Shared Random Data (PSRD) block.
"""

from uuid import UUID, uuid4
from os import urandom
from typing import Tuple
import pydantic
from bitarray import bitarray
from common.fragment import Fragment
from common.utils import bytes_to_str, str_to_bytes
from common.exceptions import (
    InvalidBlockUUIDError,
    InvalidPSRDDataError,
    InvalidPSRDIndex,
    PSRDDataAlreadyUsedError,
)


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
    _used: bitarray

    def __init__(self, block_uuid: UUID, data: bytes):
        self._block_uuid = block_uuid
        self._size = len(data)
        self._data = data
        self._used = bitarray(self._size)

    @property
    def uuid(self):
        """
        The UUID of the block.
        """
        return self._block_uuid

    @property
    def nr_used_bytes(self):
        """
        Return the number of used bytes.
        """
        return self._used.count()

    @property
    def nr_unused_bytes(self):
        """
        Return the number of unused bytes.
        """
        return self._size - self.nr_used_bytes

    def to_mgmt(self):
        """
        Get the management status.
        """
        return {
            "uuid": str(self._block_uuid),
            "size": self._size,
            "data": bytes_to_str(self._data, truncate=True),
            "nr_used_bytes": self.nr_used_bytes,
            "nr_unused_bytes": self.nr_unused_bytes,
        }

    @classmethod
    def new_with_random_data(cls, size: int) -> "Block":
        """
        Create a block, containing `size` random bytes.
        """
        assert size > 0
        uuid = uuid4()
        data = urandom(size)
        return Block(uuid, data)

    def allocate_fragment(self, desired_size: int) -> Fragment | None:
        """
        Allocate a fragment from this block. If there is some but not sufficient space, a smaller
        fragment than the size asked for is returned. If there is no space left, None is returned.
        """
        result = self.allocate_data(desired_size)
        if result is None:
            return None
        (start, size, data) = result
        return Fragment(
            block=self,
            start=start,
            size=size,
            data=data,
        )

    def allocate_data(
        self, desired_size: int
    ) -> None | Tuple[int, int, int]:  # (start, size, data)
        """
        Allocate data from the block. We try to take `desired_size` bytes from the
        block, but we accept a smaller number of bytes if there is not enough data left in the
        block. We use the first gap of unused bytes in the block (i.e. we don't try look for best
        fit or anything like that). If there is no unused data left in the block, we return None.
        """
        try:
            start = self._used.index(False)
        except ValueError:
            return None
        try:
            end = self._used.index(True, start)
        except ValueError:
            end = self._size
        size = end - start
        if size > desired_size:
            end = start + desired_size
            size = desired_size
        data = self._data[start:end]
        self._used[start:end] = True
        # Zero out allocated bytes in block
        self._data = self._data[:start] + b"\x00" * size + self._data[end:]
        return (start, size, data)

    def take_data(self, start: int, size: int) -> bytes:
        """
        Take data from the block at the specified start byte and size.
        """
        end = start + size
        if start < 0 or end > self._size:
            raise InvalidPSRDIndex(self._block_uuid, start)
        if self._used[start:end].any():
            raise PSRDDataAlreadyUsedError(self._block_uuid, start, size)
        self._used[start:end] = True
        data = self._data[start:end]
        # Zero out allocated bytes in block
        self._data = self._data[:start] + b"\x00" * size + self._data[end:]
        return data

    def give_back_data(self, start: int, data: bytes):
        """
        Give back previously taken data to the block.
        """
        # Giving back data is only used internally; the parameters are decided by the outside world.
        # Thus, if there is a problem with the parameters it is a bug: we assert rather than raise.
        size = len(data)
        assert size > 0
        assert size <= self._size
        end = start + size
        assert self._used[start:end].all()
        self._used[start:end] = False
        self._data = self._data[:start] + data + self._data[end:]

    def is_fully_used(self):
        """
        Check if all bytes in the block have been used.
        """
        return self._used.all()

    @classmethod
    def from_api(cls, api_block: APIBlock) -> "Block":
        """
        Create a Block from an APIBlock.
        """
        try:
            block_uuid = UUID(api_block.block_uuid)
        except ValueError as exc:
            raise InvalidBlockUUIDError(api_block.block_uuid) from exc
        try:
            data = str_to_bytes(api_block.data)
        except Exception as exc:
            raise InvalidPSRDDataError from exc
        return Block(block_uuid, data)

    def to_api(self) -> APIBlock:
        """
        Create an APIBLock from a Block.
        """
        return APIBlock(
            block_uuid=str(self._block_uuid),
            data=bytes_to_str(self._data),
        )
