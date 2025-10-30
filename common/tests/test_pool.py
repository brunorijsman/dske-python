"""
Unit tests for the Fragment class.
"""

from uuid import uuid4
from typing import List
from common.pool import Pool
from common.block import Block
from common.utils import bytes_to_str


def _bytes_test_pattern(size):
    return bytes([i % 255 for i in range(size)])


def _create_test_block(size):
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    return block


def _create_test_pool_and_block(block_sizes: List[int]):
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


def test_to_mgmt():
    """
    Get the management status.
    """
    pool, blocks = _create_test_pool_and_block([10, 20])
    pool_mgmt = pool.to_mgmt()
    assert pool_mgmt == {
        "blocks": [
            {
                "uuid": str(block.uuid),
                "size": block.size,
                "data": bytes_to_str(block.data, truncate=True),
                "nr_used_bytes": block.nr_used_bytes,
                "nr_unused_bytes": block.nr_unused_bytes,
            }
            for block in blocks
        ],
        "owner": str(pool.owner),
    }
