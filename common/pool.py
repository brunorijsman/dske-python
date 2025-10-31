"""
A pool of blocks.
"""

import enum
from uuid import UUID
from pydantic import PositiveInt
from .allocation import Allocation
from .block import Block
from .logging import LOGGER
from .exceptions import OutOfPreSharedRandomDataError, InvalidBlockUUIDError


class Pool:
    """
    A pool of blocks.
    """

    class Owner(enum.Enum):
        """
        Who owns the pool? The client node or the hub node? Only the owner is allowed to make
        allocations out of the pool. The non-owner only takes data out of the pool, but the peer
        decides which data is taken (i.e. the peer does the allocation).
        """

        LOCAL = 1
        PEER = 2

        def __str__(self):
            return self.name.lower()

    _name: str
    _blocks: list[Block]
    _owner: Owner

    def __init__(self, name: str, owner: Owner):
        self._name = name
        self._blocks = []
        self._owner = owner

    @property
    def owner(self) -> Owner:
        """
        Get the owner of the pool.
        """
        return self._owner

    @property
    def nr_used_bytes(self):
        """
        Return the total number of used bytes in the pool.
        """
        return sum(block.nr_used_bytes for block in self._blocks)

    @property
    def nr_unused_bytes(self):
        """
        Return the total number of unused bytes in the pool.
        """
        return sum(block.nr_unused_bytes for block in self._blocks)

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
        raise InvalidBlockUUIDError(block_uuid=str(block_uuid))

    def allocate(self, size: PositiveInt, purpose: str) -> Allocation:
        """
        Allocate an allocation from the pool. An allocation consists of one or more fragments.
        This either returns an Allocation object for the full requested `size`. Raises exception
        OutOfPreSharedRandomDataError if not enough unused bytes are available in the pool.
        """
        available = self.nr_unused_bytes
        if available < size:
            LOGGER.error(
                f"PSRD allocation failed: pool={self._name} owner={self._owner} purpose={purpose} "
                f"size={size} available={available}"
            )
            raise OutOfPreSharedRandomDataError(
                f"{self._name} {self._owner}", purpose, size, available
            )
        fragments = []
        try:
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
                    # We have allocated the full desired size; no need to look at any more blocks.
                    break
            assert (
                remaining_size == 0
            )  # We checked availability at the top of the method.
            return Allocation(fragments)
        # As far as we know because of the check at the top, there is currently no way to reach
        # this. This is just defensive programming.
        except Exception as exc:  # pragma: no cover
            # Allocation failed halfway; give back any fragments that were taken.
            for fragment in fragments:
                fragment.give_back()
            raise exc

    def delete_fully_used_blocks(self):
        """
        Delete fully used PSRD blocks from the pool.
        """
        new_blocks = [block for block in self._blocks if not block.is_fully_used()]
        self._blocks = new_blocks
