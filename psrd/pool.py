"""
A Pre-Shared Random Data (PSRD) pool.
"""

from .block import Block


class Pool:
    """
    A Pre-Shared Random Data (PSRD) pool.
    """

    _remaining_size: int
    _psrd_blocks: list[Block]

    def __init__(self):
        self._remaining_size = 0
        self._psrd_blocks = []

    def management_status(self) -> dict:
        """
        Get the management status.
        """
        return {
            "remaining_size": self._remaining_size,
            "psrd_blocks": [
                psrd_block.management_status() for psrd_block in self._psrd_blocks
            ],
        }

    def add_psrd_block(self, psrd_block: Block):
        """
        Add a PSRD block to the PSRD pool.
        """
        self._psrd_blocks.append(psrd_block)
        self._remaining_size += psrd_block.remaining_size
