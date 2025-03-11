"""
A Pre-Shared Random Data (PSRD) fragment.
"""

import common


class Fragment:
    """
    A Pre-Shared Random Data (PSRD) fragment. A contiguous range of bytes in a PSRD block.
    """

    _block: "Block"  # type: ignore TODO: do we need this?
    _start_byte: int
    _size: int
    _consumed: bool

    def __init__(self, block, start_byte, length):
        self._block = block
        self._start_byte = start_byte
        self._size = length
        self._value = None
        self._consumed = False

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

    def to_mgmt_dict(self) -> dict:
        """
        Get the management status.
        """
        return {
            "block_uuid": str(self._block.uuid),
            "start_byte": self._start_byte,
            "size": self._size,
            "value": common.bytes_to_str(self._value, truncate=True),
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
