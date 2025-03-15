"""
A Pre-Shared Random Data (PSRD) fragment.
"""

from uuid import UUID
import pydantic
from .common import bytes_to_str


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
    _start_byte: int
    _size: int
    _consumed: bool

    def __init__(self, block, start_byte, size):
        self._block = block
        self._start_byte = start_byte
        self._size = size
        self._value = None
        self._consumed = False

    @property
    def block(self):
        """
        The block that the fragment belongs to.
        """
        return self._block

    @property
    def start_byte(self):
        """
        The starting byte of the fragment.
        """
        return self._start_byte

    @property
    def size(self):
        """
        The size of the fragment in bytes.
        """
        return self._size

    @property
    def consumed(self):
        """
        Whether the fragment is consumed.
        """
        return self._consumed

    def to_mgmt(self) -> dict:
        """
        Get the management status.
        """
        return {
            "block_uuid": str(self._block.uuid),
            "start_byte": self._start_byte,
            "size": self._size,
            "value": bytes_to_str(self._value, truncate=True),
            "consumed": self._consumed,
        }

    def consume(self) -> bytes:
        """
        Consume the PSRD fragment. This requires that the fragment was previously allocated.
        Since the allocation was successful, consuming the data cannot fail. Once the data has
        consumed, it cannot be un-consumed.
        """
        assert not self._consumed
        assert self._value is None
        self._value = self._block.consume_fragment(self)
        self._consumed = True
        return self._value

    @classmethod
    def from_api(
        cls,
        api_fragment: APIFragment,
        pool: "Pool",  # type: ignore
    ) -> "Fragment":
        """
        Create a Fragment from an APIFragment.
        """
        block = pool.get_block(UUID(api_fragment.block_uuid))
        # TODO: Handle the case that the block is not found; currently exception is raised
        return Fragment(
            block=block,
            start_byte=api_fragment.start_byte,
            size=api_fragment.size,
        )

    def to_api(self) -> APIFragment:
        """
        Create an APIFragment from a Fragment.
        """
        return APIFragment(
            block_uuid=str(self._block.uuid),
            start_byte=self._start_byte,
            size=self._size,
        )
