"""
A Pre-Shared Random Data (PSRD) pool.
"""

from pydantic import PositiveInt

from .allocation import Allocation
from .block import Block


class Pool:
    """
    A Pre-Shared Random Data (PSRD) pool.
    """

    _remaining_size: int
    _blocks: list[Block]

    def __init__(self):
        self._remaining_size = 0
        self._blocks = []

    def to_mgmt_dict(self) -> dict:
        """
        Get the management status.
        """
        return {
            "remaining_size": self._remaining_size,
            "psrd_blocks": [psrd_block.to_mgmt_dict() for psrd_block in self._blocks],
        }

    def to_protocol_dict(self) -> dict:
        """
        Convert to JSON representation as used in the DSKE protocol.
        """
        # TODO
        assert False

    def add_psrd_block(self, psrd_block: Block):
        """
        Add a PSRD block to the PSRD pool.
        """
        self._blocks.append(psrd_block)
        self._remaining_size += psrd_block.remaining_size

    def allocate_allocation(self, size: PositiveInt) -> Allocation | None:
        """
        Allocate a PSRD allocation from the pool. An allocation consists of one or more fragments.
        This either returns an Allocation object for the full requested `size` or None if there is
        not enough unallocated data left in the pool.
        """
        # Collect fragments until we have what we need or until we have exhausted all blocks.
        fragments = []
        remaining_size = size
        for block in self._blocks:
            while remaining_size > 0:
                fragment = block.allocate_fragment(remaining_size)
                if fragment is None:
                    # The current block is exhausted, move on to the next block, if any.
                    break
                fragments.append(fragment)
                remaining_size -= fragment.size
            if remaining_size == 0:
                # We have allocated the full desired size; don't need to look at any more blocks.
                break
        if remaining_size > 0:
            # We didn't allocate the full desired size, deallocate the fragments we did allocate.
            for fragment in fragments:
                fragment.block.deallocate_psrd_fragment(fragment)
            return None
        # TODO: Purge any blocks that are now fully allocated. But....
        #       1. The fragments still have a back-reference to the block.
        #       2. What if the allocation is deallocated? Do we even ever allow that?
        return Allocation(fragments)
