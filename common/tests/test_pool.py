"""
Unit tests for the Fragment class.
"""

from uuid import uuid4
from typing import List
import pytest
from common.pool import Pool
from common.block import Block
from common.exceptions import InvalidBlockUUIDError, OutOfPreSharedRandomDataError
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


def test_nr_used_and_unused_bytes():
    """
    Number of unused bytes in the pool.
    """
    pool, _blocks = _create_test_pool_and_block([10, 20, 30])
    assert pool.nr_used_bytes == 0
    assert pool.nr_unused_bytes == 60
    _allocation = pool.allocate(10, purpose="test")
    assert pool.nr_used_bytes == 10
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


def test_get_block_success():
    """
    Get a block by UUID (block exists).
    """
    pool, blocks = _create_test_pool_and_block([10, 20])
    for block in blocks:
        retrieved_block = pool.get_block(block.uuid)
        assert retrieved_block == block


def test_get_block_unknown_uuid():
    """
    Get a block by UUID (no block with the given UUID).
    """
    pool, _blocks = _create_test_pool_and_block([10, 20])
    uuid = uuid4()
    with pytest.raises(InvalidBlockUUIDError):
        pool.get_block(uuid)


def test_allocate_success_empty_pool_first_block():
    """
    Allocate an allocation from a pool. The pool is empty. The allocation fits in the first block.
    """
    pool, _blocks = _create_test_pool_and_block([10, 20])
    allocation = pool.allocate(10, purpose="test")
    assert allocation is not None
    assert allocation.data == bytes.fromhex("00010203040506070809")
    assert pool.nr_used_bytes == 10


def test_allocate_success_empty_pool_two_blocks():
    """
    Allocate an allocation from a pool. The pool is empty. The allocation is spread over two blocks.
    """
    pool, _blocks = _create_test_pool_and_block([5, 5])
    allocation = pool.allocate(8, purpose="test")
    assert allocation is not None
    assert allocation.data == bytes.fromhex("0001020304000102")
    assert pool.nr_used_bytes == 8


def test_allocate_failure_insufficient_space():
    """
    Attempt to allocate an allocation from a pool. There is not enough unused data in the pool.
    """
    pool, _blocks = _create_test_pool_and_block([5, 5])
    with pytest.raises(OutOfPreSharedRandomDataError):
        pool.allocate(20, purpose="test")
    assert pool.nr_used_bytes == 0
