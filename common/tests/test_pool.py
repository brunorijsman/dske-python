"""
Unit tests for the Fragment class.
"""

from uuid import uuid4
import pytest
from common.pool import Pool
from common.exceptions import InvalidBlockUUIDError, OutOfPreSharedRandomDataError
from common.utils import bytes_to_str
from .unit_test_common import create_test_pool_and_blocks


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
    pool, _blocks = create_test_pool_and_blocks([10, 20, 30])
    assert pool.nr_used_bytes == 0
    assert pool.nr_unused_bytes == 60
    _allocation = pool.allocate(10, purpose="test")
    assert pool.nr_used_bytes == 10
    assert pool.nr_unused_bytes == 50


def test_to_mgmt():
    """
    Get the management status.
    """
    pool, blocks = create_test_pool_and_blocks([10, 20])
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
    pool, blocks = create_test_pool_and_blocks([10, 20])
    for block in blocks:
        retrieved_block = pool.get_block(block.uuid)
        assert retrieved_block == block


def test_get_block_unknown_uuid():
    """
    Get a block by UUID (no block with the given UUID).
    """
    pool, _blocks = create_test_pool_and_blocks([10, 20])
    uuid = uuid4()
    with pytest.raises(InvalidBlockUUIDError):
        pool.get_block(uuid)


def test_allocate_success_empty_pool_first_block_partial():
    """
    Allocate an allocation from a pool. The pool is empty. The allocation uses part of the first
    block.
    """
    pool, _blocks = create_test_pool_and_blocks([10, 20])
    allocation = pool.allocate(5, purpose="test")
    assert allocation is not None
    assert allocation.data == bytes.fromhex("0001020304")
    assert pool.nr_used_bytes == 5


def test_allocate_success_empty_pool_first_block_full():
    """
    Allocate an allocation from a pool. The pool is empty. The allocation uses exactly the first
    block.
    """
    pool, _blocks = create_test_pool_and_blocks([10, 20])
    allocation = pool.allocate(10, purpose="test")
    assert allocation is not None
    assert allocation.data == bytes.fromhex("00010203040506070809")
    assert pool.nr_used_bytes == 10


def test_allocate_success_empty_pool_first_block_full_second_block_partial():
    """
    Allocate an allocation from a pool. The pool is empty. The allocation is spread over two blocks.
    """
    pool, _blocks = create_test_pool_and_blocks([5, 5])
    allocation = pool.allocate(8, purpose="test")
    assert allocation is not None
    assert allocation.data == bytes.fromhex("0001020304000102")
    assert pool.nr_used_bytes == 8


def test_allocate_success_empty_pool_first_block_full_second_block_full():
    """
    Allocate an allocation from a pool. The pool is empty. The allocation is spread over two blocks.
    """
    pool, _blocks = create_test_pool_and_blocks([5, 4])
    allocation = pool.allocate(9, purpose="test")
    assert allocation is not None
    assert allocation.data == bytes.fromhex("000102030400010203")
    assert pool.nr_used_bytes == 9


# TODO: Also test re-allocation after giving back


def test_allocate_failure_insufficient_space():
    """
    Attempt to allocate an allocation from a pool. There is not enough unused data in the pool.
    """
    pool, _blocks = create_test_pool_and_blocks([5, 5])
    with pytest.raises(OutOfPreSharedRandomDataError):
        pool.allocate(20, purpose="test")
    assert pool.nr_used_bytes == 0


def test_delete_fully_used_blocks():
    """
    Delete fully used PSRD blocks from the pool.
    """
    pool, _blocks = create_test_pool_and_blocks([10, 11])
    # Allocate all of the first block and part of the second block.
    _allocation = pool.allocate(15, purpose="test1")
    assert pool.nr_used_bytes == 15
    assert pool.nr_unused_bytes == 6
    pool.delete_fully_used_blocks()
    assert pool.nr_used_bytes == 5
    assert pool.nr_unused_bytes == 6
