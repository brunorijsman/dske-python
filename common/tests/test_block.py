"""
Unit tests for the Block class.
"""

from uuid import uuid4
from common import utils
from common.block import Block


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
        "allocated": 0,
        "consumed": 0,
    }


def test_create_random_block():
    size = 100
    _block = Block.create_random_block(size)


def test_allocate_fragment_from_fresh_block():
    """
    Allocate one fragment from a block that has not had any bytes allocated yet.
    """
    block_size = 100
    fragment_size = 10
    block = _create_test_block(block_size)
    fragment = block.allocate_fragment(fragment_size)
    assert fragment.start_byte == 0
    assert fragment.size == fragment_size
    assert fragment.consumed is False


def test_allocate_multiple_fragments_from_fresh_block():
    """
    Allocate multiple fragments from a block that has not had any bytes allocated yet.
    """
    block_size = 100
    nr_fragments = 3
    fragment_size = 10
    block = _create_test_block(block_size)
    for fragment_nr in range(nr_fragments):
        fragment = block.allocate_fragment(fragment_size)
        assert fragment.start_byte == fragment_nr * fragment_size
        assert fragment.size == fragment_size
        assert fragment.consumed is False


def test_try_allocate_fragment_from_empty_block():
    """
    Try to allocate a fragment from a block that has no bytes left.
    """
    block_size = 100
    block = _create_test_block(block_size)
    additional_fragment_size = 1
    # Allocate a fragment that allocates all bytes in the block.
    fragment_a = block.allocate_fragment(block_size)
    assert fragment_a.start_byte == 0
    assert fragment_a.size == block_size
    assert fragment_a.consumed is False
    # Try to allocate another fragment, but there are no bytes left.
    fragment_b = block.allocate_fragment(additional_fragment_size)
    assert fragment_b is None


def test_try_allocate_fragment_from_block_with_insufficient_space():
    """
    Try to allocate a fragment from a block that has insufficient space.
    """
    block_size = 100
    block = _create_test_block(block_size)
    fragment_a_size = 90
    fragment_b_size = 20
    # Allocate a fragment that allocates all bytes in the block.
    fragment_a = block.allocate_fragment(fragment_a_size)
    assert fragment_a.start_byte == 0
    assert fragment_a.size == fragment_a_size
    assert fragment_a.consumed is False
    # Try to allocate another fragment, but we have fewer bytes left than asked for.
    # We should still get a fragment, just with fewer bytes.
    fragment_b = block.allocate_fragment(fragment_b_size)
    assert fragment_b.start_byte == fragment_a_size
    assert fragment_b.size == block_size - fragment_a_size
    assert fragment_b.consumed is False


def test_deallocate_fragment():
    """
    Deallocate a fragment from a block. Test re-allocating from a gap in a block.
    """
    block_size = 100
    fragment_a_size = 10
    fragment_b_size = 20
    fragment_c_size = 30
    # Some conditions to make the test case work as intended
    assert fragment_a_size + fragment_b_size <= block_size
    assert fragment_c_size > fragment_a_size
    # The sequence of actions is:
    # 1. Allocate fragment a.
    # 2. Allocate fragment b.
    # 3. Deallocate fragment a.
    # 4. Allocate fragment c. Note that it does *not* fit in the gap left by fragment a.
    #    So we get less than we asked for.
    block = _create_test_block(block_size)
    # Allocate fragment a
    fragment_a = block.allocate_fragment(fragment_a_size)
    assert fragment_a.start_byte == 0
    assert fragment_a.size == fragment_a_size
    assert fragment_a.consumed is False
    # Allocate fragment b
    fragment_b = block.allocate_fragment(fragment_b_size)
    assert fragment_b.start_byte == fragment_a_size
    assert fragment_b.size == fragment_b_size
    assert fragment_b.consumed is False
    # Deallocate fragment a
    block.deallocate_fragment(fragment_a)
    # Attempt to allocate fragment c; we get less than we asked for
    fragment_c = block.allocate_fragment(fragment_c_size)
    assert fragment_c.start_byte == 0
    assert fragment_c.size == fragment_a_size
    assert fragment_c.consumed is False
