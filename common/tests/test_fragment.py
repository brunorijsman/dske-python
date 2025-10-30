"""
Unit tests for the Fragment class.
"""

from uuid import uuid4
from common.block import Block
from common.fragment import Fragment
from common.utils import bytes_to_str


def _bytes_test_pattern(size):
    return bytes([i % 255 for i in range(size)])


def _create_test_block(size):
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    return block


def test_fragment_init():
    """
    Initialize a fragment.
    """
    block = _create_test_block(100)
    _fragment = Fragment(
        block=block,
        start=0,
        size=10,
        data=bytes.fromhex("00010203040506070809"),
    )


def test_allocate_full():
    """
    Allocate a fragment. Requested allocation is fully available.
    """
    block = _create_test_block(100)
    fragment = Fragment.allocate(block, 10)
    assert fragment.block == block
    assert fragment.start == 0
    assert fragment.size == 10
    assert fragment.data == bytes.fromhex("00010203040506070809")


def test_allocate_partial():
    """
    Allocate a fragment. Requested allocation is partially available.
    """
    block = _create_test_block(5)
    fragment = Fragment.allocate(block, 10)
    assert fragment.block == block
    assert fragment.start == 0
    assert fragment.size == 5
    assert fragment.data == bytes.fromhex("0001020304")


def test_allocate_none():
    """
    Allocate a fragment. No allocation is available.
    """
    block = _create_test_block(5)
    fragment = Fragment.allocate(block, 5)
    assert fragment.block == block
    assert fragment.start == 0
    assert fragment.size == 5
    assert fragment.data == bytes.fromhex("0001020304")
    assert Fragment.allocate(block, 5) is None


def test_give_back_success():
    """
    Give a fragment back to the block.
    """
    # pylint: disable=protected-access
    block = _create_test_block(16)
    assert block.nr_used_bytes == 0
    # Allocate 5 bytes for fragment A
    assert block._data == bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    fragment_a = Fragment.allocate(block, 5)
    assert fragment_a.block == block
    assert fragment_a.start == 0
    assert fragment_a.size == 5
    assert fragment_a.data == bytes.fromhex("0001020304")
    assert block.nr_used_bytes == 5
    assert block._data == bytes.fromhex("000000000005060708090a0b0c0d0e0f")
    # Allocate 3 bytes for fragment B
    fragment_b = Fragment.allocate(block, 3)
    assert fragment_b.block == block
    assert fragment_b.start == 5
    assert fragment_b.size == 3
    assert fragment_b.data == bytes.fromhex("050607")
    assert block.nr_used_bytes == 8
    assert block._data == bytes.fromhex("000000000000000008090a0b0c0d0e0f")
    # Give fragment A back
    fragment_a.give_back()
    assert fragment_a.data is None
    assert block.nr_used_bytes == 3
    assert block._data == bytes.fromhex("000102030400000008090a0b0c0d0e0f")


def test_fragment_to_mgmt():
    """
    Get the management status of a fragment.
    """
    block = _create_test_block(5)
    fragment = Fragment.allocate(block, 5)
    fragment_mgmt = fragment.to_mgmt()
    assert fragment_mgmt == {
        "block_uuid": str(block.uuid),
        "start": 0,
        "size": 5,
        "data": bytes_to_str(bytes.fromhex("0001020304")),
    }
