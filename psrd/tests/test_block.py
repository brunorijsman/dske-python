"""
Unit tests for the Block class.
"""

from uuid import uuid4

import common
from psrd.block import Block


# pylint: disable=missing-function-docstring


def _bytes_test_pattern(size):
    return bytes([i % 255 for i in range(size)])


def test_block_init():
    uuid = uuid4()
    data = _bytes_test_pattern(1000)
    _block = Block(uuid, data)


def test_block_properties():
    uuid = uuid4()
    data = _bytes_test_pattern(1000)
    block = Block(uuid, data)
    assert block.uuid == uuid
    assert block.remaining_size == 1000


def test_block_to_management_json():
    uuid = uuid4()
    data = _bytes_test_pattern(20)
    block = Block(uuid, data)
    management_json = block.to_management_json()
    assert management_json == {
        "uuid": str(uuid),
        "original_size": 20,
        "remaining_size": 20,
        "data": common.bytes_to_str(data, truncate=True),
    }


def test_block_to_protocol_json():
    uuid = uuid4()
    data = _bytes_test_pattern(20)
    block = Block(uuid, data)
    protocol_json = block.to_protocol_json()
    assert protocol_json == {
        "uuid": str(uuid),
        "data": common.bytes_to_str(data),
    }


def test_block_from_protocol_json():
    uuid = uuid4()
    data = _bytes_test_pattern(20)
    protocol_json = {
        "uuid": str(uuid),
        "data": common.bytes_to_str(data),
    }
    block = Block.from_protocol_json(protocol_json)
    assert block.uuid == uuid
    assert block.remaining_size == 20
