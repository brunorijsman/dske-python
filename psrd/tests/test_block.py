"""
Unit tests for the Block class.
"""

from uuid import uuid4

import common
from psrd.block import Block


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
    assert block.remaining_size == size


def test_block_to_management_json():
    size = 20
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    management_json = block.to_management_json()
    assert management_json == {
        "uuid": str(uuid),
        "original_size": size,
        "remaining_size": size,
        "data": common.bytes_to_str(data, truncate=True),
    }


def test_block_to_protocol_json():
    size = 20
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    protocol_json = block.to_protocol_json()
    assert protocol_json == {
        "uuid": str(uuid),
        "data": common.bytes_to_str(data),
    }


def test_block_from_protocol_json():
    size = 20
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    protocol_json = {
        "uuid": str(uuid),
        "data": common.bytes_to_str(data),
    }
    block = Block.from_protocol_json(protocol_json)
    assert block.uuid == uuid
    assert block.remaining_size == size


def test_create_random_psrd_block():
    size = 100
    block = Block.create_random_psrd_block(size)
    assert block.remaining_size == size


def test_allocate_psrd_fragment_from_fresh_block():
    """
    Allocate one fragment from a block that has not had any bytes allocated yet.
    """
    block_size = 100
    fragment_size = 10
    block = _create_test_block(block_size)
    fragment = block.allocate_psrd_fragment(fragment_size)
    assert fragment.start_byte == 0
    assert fragment.size == fragment_size
    assert fragment.consumed is False


def test_allocate_multiple_psrd_fragments_from_fresh_block():
    """
    Allocate multiple fragments from a block that has not had any bytes allocated yet.
    """
    block_size = 100
    nr_fragments = 3
    fragment_size = 10
    block = _create_test_block(block_size)
    for fragment_nr in range(nr_fragments):
        fragment = block.allocate_psrd_fragment(fragment_size)
        assert fragment.start_byte == fragment_nr * fragment_size
        assert fragment.size == fragment_size
        assert fragment.consumed is False
