"""
Unit tests for the Block class.
"""

from uuid import uuid4
import pytest
from common.utils import bytes_to_str
from common.block import APIBlock, Block
from common.exceptions import (
    InvalidBlockUUIDError,
    InvalidPSRDDataError,
    InvalidPSRDIndex,
    PSRDDataAlreadyUsedError,
)


def _bytes_test_pattern(size):
    return bytes([i % 255 for i in range(size)])


def _create_test_block(size):
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    return block


def test_init():
    """
    Initialize a block.
    """
    size = 1000
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    _block = Block(uuid, data)


def test_properties():
    """ "
    Test the properties of a block.
    """
    size = 1000
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    assert block.uuid == uuid
    assert block.size == size
    assert block.data == data
    assert block.nr_unused_bytes == size


def test_to_mgmt():
    """
    Get the management status.
    """
    size = 20
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    block_mgmt = block.to_mgmt()
    assert block_mgmt == {
        "uuid": str(uuid),
        "size": 20,
        "data": bytes_to_str(data, truncate=True),
        "nr_used_bytes": 0,
        "nr_unused_bytes": size,
    }


def test_create_random_block():
    """
    Create a block with random data.
    """
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
    # pylint: disable=protected-access
    block = _create_test_block(5)
    assert block._data == bytes.fromhex("0001020304")
    (start, size, data) = block.allocate_data(3)
    assert start == 0
    assert size == 3
    assert data == bytes.fromhex("000102")
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


def test_return_data():
    """
    Return taken data back to block.
    """
    # pylint: disable=protected-access
    # Create a block
    block = _create_test_block(10)
    assert block._data == bytes.fromhex("00010203040506070809")
    assert block.nr_used_bytes == 0
    # Allocate 3 bytes
    (start, size, data) = block.allocate_data(3)
    assert start == 0
    assert size == 3
    assert data == bytes.fromhex("000102")
    assert block._data == bytes.fromhex("00000003040506070809")
    assert block.nr_used_bytes == 3
    # Allocate 3 more
    (start, size, data) = block.allocate_data(3)
    assert start == 3
    assert size == 3
    assert data == bytes.fromhex("030405")
    assert block._data == bytes.fromhex("00000000000006070809")
    assert block.nr_used_bytes == 6
    # Allocate 3 more yet again
    (start, size, data) = block.allocate_data(3)
    assert start == 6
    assert size == 3
    assert data == bytes.fromhex("060708")
    assert block._data == bytes.fromhex("00000000000000000009")
    assert block.nr_used_bytes == 9
    # Return the middle 3 bytes
    block.give_back_data(3, bytes.fromhex("030405"))
    assert block._data == bytes.fromhex("00000003040500000009")
    assert block.nr_used_bytes == 6


def test_allocate_fragment_full():
    """
    Allocate a fragment. Requested allocation is fully available.
    """
    block = _create_test_block(100)
    fragment = block.allocate_fragment(10)
    assert fragment.block == block
    assert fragment.start == 0
    assert fragment.size == 10
    assert fragment.data == bytes.fromhex("00010203040506070809")


def test_allocate_fragment_partial():
    """
    Allocate a fragment. Requested allocation is partially available.
    """
    block = _create_test_block(5)
    fragment = block.allocate_fragment(10)
    assert fragment.block == block
    assert fragment.start == 0
    assert fragment.size == 5
    assert fragment.data == bytes.fromhex("0001020304")


def test_allocate_fragment_none():
    """
    Allocate a fragment. No allocation is available.
    """
    block = _create_test_block(5)
    fragment = block.allocate_fragment(5)
    assert fragment.block == block
    assert fragment.start == 0
    assert fragment.size == 5
    assert fragment.data == bytes.fromhex("0001020304")
    assert block.allocate_fragment(5) is None


def test_is_fully_used():
    """
    Check if all bytes in the block have been used.
    """
    block = _create_test_block(10)
    assert not block.is_fully_used()
    (start, size, data) = block.allocate_data(10)
    assert start == 0
    assert size == 10
    assert data == bytes.fromhex("00010203040506070809")
    assert block.is_fully_used()


def test_to_api():
    """
    Create an APIBlock for a Block.
    """
    block = _create_test_block(10)
    api_block = block.to_api()
    assert api_block.block_uuid == str(block.uuid)
    assert api_block.data == bytes_to_str(_bytes_test_pattern(10))


def test_from_api_success():
    """
    Create a Block from a valid APIBlock.
    """
    uuid = uuid4()
    data = _bytes_test_pattern(10)
    api_block = APIBlock(block_uuid=str(uuid), data=bytes_to_str(data))
    block = Block.from_api(api_block)
    assert block.uuid == uuid
    assert block.nr_unused_bytes == 10


def test_from_api_bad_uuid():
    """
    Attempt to create a Block from a bad APIBlock (invalid block UUID).
    """
    data = _bytes_test_pattern(10)
    api_block = APIBlock(block_uuid="bad-uuid", data=bytes_to_str(data))
    with pytest.raises(InvalidBlockUUIDError):
        _block = Block.from_api(api_block)


def test_from_api_bad_data():
    """
    Attempt to create a Block from a bad APIBlock (invalid data).
    """
    uuid = uuid4()
    api_block = APIBlock(block_uuid=str(uuid), data="bad-data")
    with pytest.raises(InvalidPSRDDataError):
        _block = Block.from_api(api_block)
