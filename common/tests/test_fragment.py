"""
Unit tests for the Fragment class.
"""

from uuid import uuid4
from common.block import Block
from common.fragment import Fragment
from common.utils import bytes_to_str


# pylint: disable=missing-function-docstring


def _bytes_test_pattern(size):
    return bytes([i % 255 for i in range(size)])


def _create_test_block(size):
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    return block


def test_fragment_init():
    block = _create_test_block(100)
    _fragment = Fragment(
        block=block,
        start=0,
        size=10,
        data=bytes.fromhex("00010203040506070809"),
    )


def test_fragment_allocate_full():
    block = _create_test_block(100)
    fragment = Fragment.allocate(block, 10)
    assert fragment.block == block
    assert fragment.start == 0
    assert fragment.size == 10
    assert fragment.data == bytes.fromhex("00010203040506070809")


def test_fragment_allocate_partial():
    block = _create_test_block(5)
    fragment = Fragment.allocate(block, 10)
    assert fragment.block == block
    assert fragment.start == 0
    assert fragment.size == 5
    assert fragment.data == bytes.fromhex("0001020304")


def test_fragment_allocate_none():
    block = _create_test_block(5)
    fragment = Fragment.allocate(block, 5)
    assert fragment.block == block
    assert fragment.start == 0
    assert fragment.size == 5
    assert fragment.data == bytes.fromhex("0001020304")
    assert Fragment.allocate(block, 5) is None


def test_fragment_to_mgmt():
    block = _create_test_block(5)
    fragment = Fragment.allocate(block, 5)
    fragment_mgmt = fragment.to_mgmt()
    assert fragment_mgmt == {
        "block_uuid": str(block.uuid),
        "start": 0,
        "size": 5,
        "data": bytes_to_str(bytes.fromhex("0001020304")),
    }
