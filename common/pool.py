"""
A pool of blocks.
"""

import enum
from uuid import UUID
from pydantic import PositiveInt
from .allocation import Allocation
from .block import Block


# TODO: Unit tests for newly added _owner attribute.


class OutOfPreSharedRandomDataError(Exception):
    """
    Out of Pre-Shared Random Data (PSRD). We tried to allocated some pre-shared random data from
    a pool, but the pool did not contain enough free data to fulfill the allocation request.
    """


class Pool:
    """
    A pool of blocks.
    """

    class Owner(enum.Enum):
        """
        Who owns the pool? The client node or the hub node? Only the owner is allowed to make
        allocations out of the pool. The non-owner is only allowed to consume allocations made
        by the peer node, who is the owner of the pool.
        """

        LOCAL = 1
        PEER = 2

    _blocks: list[Block]
    _owner: Owner

    def __init__(self, owner: Owner):
        self._blocks = []
        self._owner = owner

    @property
    def owner(self) -> Owner:
        """
        Get the owner of the pool.
        """
        return self._owner

    @property
    def bytes_available(self):
        """
        Return the number of bytes available for allocation in the pool.
        """
        return sum(block.bytes_available_for_allocation for block in self._blocks)

    def to_mgmt(self) -> dict:
        """
        Get the management status.
        """
        return {
            "blocks": [block.to_mgmt() for block in self._blocks],
            "owner": str(self._owner),
        }

    def add_block(self, block: Block):
        """
        Add a block to the pool.
        """
        self._blocks.append(block)

    def get_block(self, block_uuid: UUID) -> Block:
        """
        Get a block by block UUID.
        """
        for block in self._blocks:
            if block.uuid == block_uuid:
                return block
        # TODO: Better exception type
        raise ValueError(f"Block with UUID {block_uuid} not found")

    def allocate(self, size: PositiveInt) -> Allocation:
        """
        Allocate an allocation from the pool. An allocation consists of one or more fragments.
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
                fragment.block.deallocate_fragment(fragment)
            raise OutOfPreSharedRandomDataError()
        return Allocation(fragments)

    def mark_allocation_allocated(self, allocation: Allocation):
        """
        Mark an allocation as allocated in the pool. This is needed when the allocation was received
        from the other side instead of being allocated locally.
        """
        for fragment in allocation.fragments:
            fragment.block.mark_fragment_allocated(fragment)

    def delete_fully_consumed_blocks(self):
        """
        Delete fully consumed PSRD blocks from the pool.
        """
        self._blocks = [
            block for block in self._blocks if not block.is_fully_consumed()
        ]
