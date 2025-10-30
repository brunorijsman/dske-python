"""
A Pre-Shared Random Data (PSRD) fragment.
"""

from uuid import UUID
import pydantic
from common.exceptions import InvalidBlockUUIDError, InvalidEncodedFragment
from . import utils


class APIFragment(pydantic.BaseModel):
    """
    Representation of a PSRD fragment as used in API calls.
    """

    block_uuid: str
    start: int
    size: int


class Fragment:
    """
    A PSRD fragment: a contiguous range of bytes within one PSRD block.
    """

    _block: "Block"  # type: ignore
    _start: int
    _size: int
    _data: bytes | None  # None means the fragment has been returned to the block

    def __init__(self, block, start, size, data):
        # Don't call this directly. Instead use one of the following:
        #   Block.allocate_fragment
        #   Fragment.from_api
        #   Fragment.from_enc_str
        self._block = block
        self._start = start
        self._size = size
        self._data = data

    @property
    def block(self):
        """
        The block that the fragment belongs to.
        """
        return self._block

    @property
    def start(self):
        """
        The starting byte with the block the fragment was taken from.
        """
        return self._start

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

    def give_back(self):
        """
        Return the fragment to the block it was taken from.
        """
        assert self._data is not None, "Attempt to return fragment twice"
        self._block.give_back_data(self._start, self._data)
        self._data = None

    def to_mgmt(self) -> dict:
        """
        Get the management status.
        """
        return {
            "block_uuid": str(self._block.uuid),
            "start": self._start,
            "size": self._size,
            "data": utils.bytes_to_str(self._data, truncate=True),
        }

    def to_api(self) -> APIFragment:
        """
        Create an APIFragment from a Fragment.
        """
        return APIFragment(
            block_uuid=str(self._block.uuid),
            start=self._start,
            size=self._size,
        )

    @staticmethod
    def from_api(
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
        data = block.take_data(api_fragment.start, api_fragment.size)
        return Fragment(
            block=block,
            start=api_fragment.start,
            size=api_fragment.size,
            data=data,
        )

    def to_enc_str(self) -> str:
        """
        Get a string representation of the fragment that can be used in HTTP headers or URL
        parameters.
        The format of the string is: <block_uuid>:<start_byte>:<size>
        """
        return f"{self._block.uuid}:{self._start}:{self._size}"

    @staticmethod
    def from_enc_str(
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
            raise InvalidEncodedFragment(encoded_fragment=enc_str)
        block_uuid_str, start_byte_str, size_str = parts
        try:
            block_uuid = UUID(block_uuid_str)
        except ValueError as exc:
            raise InvalidBlockUUIDError(block_uuid=block_uuid_str) from exc
        block = pool.get_block(block_uuid)
        try:
            start = int(start_byte_str)
        except ValueError as exc:
            raise InvalidEncodedFragment(encoded_fragment=enc_str) from exc
        try:
            size = int(size_str)
        except ValueError as exc:
            raise InvalidEncodedFragment(encoded_fragment=enc_str) from exc
        data = block.take_data(start, size)
        return Fragment(block=block, start=start, size=size, data=data)
