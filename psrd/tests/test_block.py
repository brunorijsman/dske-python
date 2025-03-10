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


def test_block_management_status():
    uuid = uuid4()
    data = _bytes_test_pattern(20)
    block = Block(uuid, data)
    management_status = block.management_status()
    assert management_status == {
        "uuid": str(uuid),
        "original_size": 20,
        "remaining_size": 20,
        "data": common.bytes_to_str(data, truncate=True),
    }
