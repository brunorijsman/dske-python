"""
A Pre-Shared Random Data (PSRD) pool.
"""

from .psrd_block import PSRDBlock


class PSRDPool:
    """
    A Pre-Shared Random Data (PSRD) pool.
    """

    _remaining_size: int
    _psrd_blocks: list[PSRDBlock]

    def __init__(self):
        self._remaining_size = 0
        self._psrd_blocks = []

    def add_psrd_block(self, psrd_block: PSRDBlock):
        """
        Add a PSRD block to the PSRD pool.
        """
        self._psrd_blocks.append(psrd_block)
        self._remaining_size += psrd_block.remaining_size
