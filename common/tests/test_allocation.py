"""
Unit tests for the Allocation class.
"""

from common.allocation import Allocation
from common.fragment import Fragment
from common.utils import bytes_to_str
from .unit_test_common import create_test_block, create_test_pool_and_blocks


def test_init_and_properties():
    """
    Initialize an allocation.
    """
    block = create_test_block(100)
    fragment = Fragment(
        block=block,
        start=0,
        size=10,
        data=bytes.fromhex("00010203040506070809"),
    )
    allocation = Allocation(fragments=[fragment])
    assert allocation.fragments == [fragment]
    assert allocation.data == bytes.fromhex("00010203040506070809")


def test_give_back():
    """
    Give back an allocation.
    """
    # pylint: disable=protected-access
    pool, blocks = create_test_pool_and_blocks([10, 6])
    assert blocks[0]._data == bytes.fromhex("00010203040506070809")
    assert blocks[1]._data == bytes.fromhex("000102030405")
    allocation = pool.allocate(5, purpose="test")
    assert allocation is not None
    assert allocation.data == bytes.fromhex("0001020304")
    assert pool.nr_used_bytes == 5
    assert blocks[0]._data == bytes.fromhex("00000000000506070809")
    assert blocks[1]._data == bytes.fromhex("000102030405")
    allocation.give_back()
    assert pool.nr_used_bytes == 0
    assert blocks[0]._data == bytes.fromhex("00010203040506070809")
    assert blocks[1]._data == bytes.fromhex("000102030405")


def test_to_mgmt():
    """
    Get the management status.
    """
    pool, blocks = create_test_pool_and_blocks([5, 10])
    allocation = pool.allocate(8, purpose="test")
    allocation_mgmt = allocation.to_mgmt()
    assert allocation_mgmt == {
        "fragments": [
            {
                "block_uuid": str(blocks[0].uuid),
                "data": "AAECAwQ=",  # base64 for 0001020304
                "size": 5,
                "start": 0,
            },
            {
                "block_uuid": str(blocks[1].uuid),
                "data": "AAEC",  # base64 for 0001
                "size": 3,
                "start": 0,
            },
        ],
    }
