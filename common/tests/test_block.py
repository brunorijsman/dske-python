"""
Unit tests for the Block class.
"""

from uuid import uuid4

import pytest
from common import utils
from common.block import Block
from common.exceptions import InvalidPSRDIndex, PSRDDataAlreadyUsedError


# pylint: disable=missing-function-docstring


def _bytes_test_pattern(size):
    return bytes([i % 255 for i in range(size)])


def _create_test_block(size):
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    return block


def test_block_init():
    size = 1000
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    _block = Block(uuid, data)


def test_block_properties():
    size = 1000
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    assert block.uuid == uuid
    assert block.nr_unused_bytes == size


def test_block_to_mgmt():
    size = 20
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    management_json = block.to_mgmt()
    assert management_json == {
        "uuid": str(uuid),
        "size": 20,
        "data": utils.bytes_to_str(data, truncate=True),
        "nr_used_bytes": 0,
        "nr_unused_bytes": size,
    }


def test_create_random_block():
    size = 100
    _block = Block.new_with_random_data(size)


def test_allocate_data_full():
    """
    Allocate data from block: full requested allocation is fully available.
    """
    block = _create_test_block(100)
    (start, size, data) = block.allocate_data(10)
    assert start == 0
    assert size == 10
    assert data == bytes.fromhex("00010203040506070809")


def test_allocate_data_partial():
    """
    Allocate data from block: full requested allocation is partially available.
    """
    block = _create_test_block(9)
    (start, size, data) = block.allocate_data(90)
    assert start == 0
    assert size == 9
    assert data == bytes.fromhex("000102030405060708")


def test_allocate_data_bytes_zeroed():
    """
    Allocate data from block: bytes in the block are zeroed after allocation.
    """
    block = _create_test_block(5)
    assert block._data == bytes.fromhex("0001020304")
    (start, size, data) = block.allocate_data(3)
    assert start == 0
    assert size == 3
    assert data == bytes.fromhex("000102")
    # pylint: disable=protected-access
    assert block._data == bytes.fromhex("0000000304")


def test_allocate_data_full_full():
    """
    Allocate data twice from a block: first requested allocation is fully available, second
    requested allocation is also fully available.
    """
    block = _create_test_block(100)
    (start, size, data) = block.allocate_data(10)
    assert start == 0
    assert size == 10
    assert data == bytes.fromhex("00010203040506070809")
    (start, size, data) = block.allocate_data(5)
    assert start == 10
    assert size == 5
    assert data == bytes.fromhex("0a0b0c0d0e")


def test_allocate_data_full_partial():
    """
    Allocate data twice from a block: first requested allocation is fully available, second
    requested allocation is also fully available.
    """
    block = _create_test_block(12)
    (start, size, data) = block.allocate_data(10)
    assert start == 0
    assert size == 10
    assert data == bytes.fromhex("00010203040506070809")
    (start, size, data) = block.allocate_data(5)
    assert start == 10
    assert size == 2
    assert data == bytes.fromhex("0a0b")


def test_allocate_data_full_none():
    """
    Allocate data twice from a block: first requested allocation is fully available, second
    requested allocation is also fully available.
    """
    block = _create_test_block(10)
    (start, size, data) = block.allocate_data(10)
    assert start == 0
    assert size == 10
    assert data == bytes.fromhex("00010203040506070809")
    assert block.allocate_data(5) is None


def test_take_data_all_free():
    """
    Take data from block: all requested data is free.
    """
    block = _create_test_block(10)
    data = block.take_data(2, 5)
    assert data == bytes.fromhex("0203040506")
    assert block.nr_unused_bytes == 5


def test_take_data_invalid_start_index():
    """
    Take data from block: invalid start index.
    """
    block = _create_test_block(10)
    with pytest.raises(InvalidPSRDIndex):
        _data = block.take_data(-1, 5)
    with pytest.raises(InvalidPSRDIndex):
        _data = block.take_data(10, 5)


def test_take_data_already_in_use():
    """
    Take data from block: already in use.
    """
    block = _create_test_block(10)
    (start, size, data) = block.allocate_data(5)
    assert start == 0
    assert size == 5
    assert data == bytes.fromhex("0001020304")
    # Full overlap
    with pytest.raises(PSRDDataAlreadyUsedError):
        _data = block.take_data(0, 5)
    # Partial overlap
    with pytest.raises(PSRDDataAlreadyUsedError):
        _data = block.take_data(2, 1)
