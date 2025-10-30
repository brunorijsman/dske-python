"""
Unit tests for the Allocation class.
"""

from uuid import uuid4
from common.allocation import Allocation
from common.block import Block
from common.fragment import Fragment


def _bytes_test_pattern(size):
    return bytes([i % 255 for i in range(size)])


def _create_test_block(size):
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    return block


def test_init():
    """
    Initialize an allocation.
    """
    block = _create_test_block(100)
    fragment = Fragment(
        block=block,
        start=0,
        size=10,
        data=bytes.fromhex("00010203040506070809"),
    )
    _allocation = Allocation(fragments=[fragment])
