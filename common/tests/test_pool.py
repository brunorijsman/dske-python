"""
Unit tests for the Fragment class.
"""

from uuid import uuid4
from common.pool import Pool
from common.block import Block


def _bytes_test_pattern(size):
    return bytes([i % 255 for i in range(size)])


def _create_test_block(size):
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    return block


def _create_test_pool_and_block(block_sizes: [int]):
    pool = Pool(name="test_pool", owner=Pool.Owner.LOCAL)
    blocks = []
    for block_size in block_sizes:
        block = _create_test_block(block_size)
        pool.add_block(block)
        blocks.append(block)
    return (pool, blocks)


def test_init():
    """
    Initialize a pool.
    """
    _pool = Pool(name="test_pool", owner=Pool.Owner.LOCAL)


def test_properties():
    """
    Properties of the pool.
    """
    pool = Pool(name="test_pool", owner=Pool.Owner.LOCAL)
    assert pool.owner == Pool.Owner.LOCAL


def test_nr_unused_bytes():
    """
    Number of unused bytes in the pool.
    """
    pool, _blocks = _create_test_pool_and_block([10, 20, 30])
    assert pool.nr_unused_bytes == 60
    _allocation = pool.allocate(10, purpose="test")
    assert pool.nr_unused_bytes == 50
