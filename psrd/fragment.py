"""
A Pre-Shared Random Data (PSRD) fragment.
"""


class Fragment:
    """
    A Pre-Shared Random Data (PSRD) fragment.
    """

    _block: "Block"  # type: ignore
    _start_byte: int
    _length: int

    def __init__(self, block, start_byte, length):
        self._block = block
        self._start_byte = start_byte
        self._length = length
