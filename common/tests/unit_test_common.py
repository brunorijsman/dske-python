"""
Common code for the unit tests in the common module.
"""

from uuid import uuid4
from typing import List
from common.block import Block
from common.pool import Pool


def bytes_test_pattern(size):
    """
    Generate a test pattern of bytes.
    """
    return bytes([i % 255 for i in range(size)])


def create_test_block(size):
    """
    Create a test block with the given size.
    """
    uuid = uuid4()
    data = bytes_test_pattern(size)
    block = Block(uuid, data)
    return block


def create_test_pool_and_blocks(block_sizes: List[int]):
    """
    Create a test pool with blocks of the given sizes.
    """
    pool = Pool(name="test_pool", owner=Pool.Owner.LOCAL)
    blocks = []
    for block_size in block_sizes:
        block = create_test_block(block_size)
        pool.add_block(block)
        blocks.append(block)
    return (pool, blocks)
