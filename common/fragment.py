"""
A Pre-Shared Random Data (PSRD) fragment.
"""

from uuid import UUID
import pydantic
from common.exceptions import InvalidBlockUUIDError
from . import utils


class APIFragment(pydantic.BaseModel):
    """
    Representation of a PSRD fragment as used in API calls.
    """

    block_uuid: str
    start_byte: int
    size: int


class Fragment:
    """
    A PSRD fragment: a contiguous range of bytes within one PSRD block.
    """

    _block: "Block"  # type: ignore
    _start_in_block: int
    _size: int
    _data: bytes | None  # None means the fragment has been returned to the block

    def __init__(self, block, start_in_block, size, data):
        self._block = block
        self._start_in_block = start_in_block
        self._size = size
        self._data = data

    @property
    def block(self):
        """
        The block that the fragment belongs to.
        """
        return self._block

    @property
    def start_in_block(self):
        """
        The starting byte with the block the fragment was taken from.
        """
        return self._start_in_block

    @property
    def size(self):
        """
        The size of the fragment in bytes.
        """
        return self._size

    @property
    def data(self):
        """
        The data in the fragment.
        """
        return self._data

    def to_mgmt(self) -> dict:
        """
        Get the management status.
        """
        return {
            "block_uuid": str(self._block.uuid),
            "start_in_block": self._start_in_block,
            "size": self._size,
            "data": utils.bytes_to_str(self._data, truncate=True),
        }

    def mark_as_returned_to_block(self):
        """
        Mark the fragment as returned to the pool.
        """
        self._data = None

    @property
    def is_returned_to_block(self) -> bool:
        """
        Has the fragment been returned to the block?
        """
        return self._data is None

    @classmethod
    def from_api(
        cls,
        api_fragment: APIFragment,
        pool: "Pool",  # type: ignore
    ) -> "Fragment":
        """
        Create a Fragment from an APIFragment.
        """
        try:
            block_uuid = UUID(api_fragment.block_uuid)
        except ValueError as exc:
            raise InvalidBlockUUIDError(block_uuid=api_fragment.block_uuid) from exc
        block = pool.get_block(block_uuid)
        data = block.take_data(api_fragment.start_byte, api_fragment.size)
        return Fragment(
            block=block,
            start_in_block=api_fragment.start_byte,
            size=api_fragment.size,
            data=data,
        )

    @classmethod
    def from_enc_str(
        cls,
        enc_str: str,
        pool: "Pool",  # type: ignore
    ) -> "Fragment":
        """
        Create a Fragment from an encoded string as used in an HTTP header or URL parameter.
        The format of the string is: <block_uuid>:<start_byte>:<size>
        """
        # TODO: Add expected_max_size parameter to avoid insane large sizes.
        parts = enc_str.split(":")
        if len(parts) != 3:
            raise ValueError(f"Invalid fragment parameter string: {enc_str}")
        block_uuid_str, start_byte_str, size_str = parts
        block = pool.get_block(UUID(block_uuid_str))
        if block is None:
            raise ValueError(f"Block not found: {block_uuid_str}")
        start_byte = int(start_byte_str)
        size = int(size_str)
        data = block.take_data(start_byte, size)
        return Fragment(block=block, start_in_block=start_byte, size=size, data=data)

    def to_api(self) -> APIFragment:
        """
        Create an APIFragment from a Fragment.
        """
        return APIFragment(
            block_uuid=str(self._block.uuid),
            start_byte=self._start_in_block,
            size=self._size,
        )

    def to_enc_str(self) -> str:
        """
        Get a string representation of the fragment that can be used in HTTP headers or URL
        parameters.
        The format of the string is: <block_uuid>:<start_byte>:<size>
        """
        return f"{self._block.uuid}:{self._start_in_block}:{self._size}"
