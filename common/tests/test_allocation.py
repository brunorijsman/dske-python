"""
Unit tests for the Allocation class.
"""

import pytest
from common.allocation import Allocation, APIAllocation
from common.exceptions import (
    InvalidBlockUUIDError,
    InvalidEncodedFragment,
    InvalidPSRDIndex,
)
from common.fragment import APIFragment, Fragment
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


def test_to_api():
    """
    Create an APIAllocation for an Allocation.
    """
    pool, blocks = create_test_pool_and_blocks([5, 10])
    allocation = pool.allocate(8, purpose="test")
    api_allocation = allocation.to_api()
    assert api_allocation.fragments == [
        APIFragment(block_uuid=str(blocks[0].uuid), start=0, size=5),
        APIFragment(block_uuid=str(blocks[1].uuid), start=0, size=3),
    ]


def test_from_api_success():
    """
    Create an Allocation from a valid APIAllocation.
    """
    # pylint: disable=protected-access
    pool, blocks = create_test_pool_and_blocks([10])
    api_fragment = APIFragment(block_uuid=str(blocks[0].uuid), start=0, size=5)
    api_allocation = APIAllocation(fragments=[api_fragment])
    allocation = Allocation.from_api(api_allocation, pool)
    assert len(allocation.fragments) == 1
    fragment = allocation.fragments[0]
    assert fragment.block == blocks[0]
    assert fragment.start == 0
    assert fragment.size == 5
    assert fragment.data == bytes.fromhex("0001020304")


def test_from_api_bad_fragment():
    """
    Attempt to create an Allocation from a bad APIAllocation: one of the fragments has an invalid
    block UUID.
    """
    pool, _blocks = create_test_pool_and_blocks([10])
    api_fragment = APIFragment(block_uuid="not-a-uuid", start=0, size=5)
    _api_allocation = APIAllocation(fragments=[api_fragment])
    with pytest.raises(InvalidBlockUUIDError):
        _allocation = Allocation.from_api(_api_allocation, pool)


def test_from_api_second_fragment_is_bad():
    """
    Attempt to create an Allocation from bad APIAllocations. The first APIFragment is valid. The
    second has an invalid block size. Make sure the first fragment is properly given back to the
    pool (all-or-nothing behavior).
    """
    # pylint: disable=protected-access
    pool, blocks = create_test_pool_and_blocks([10])
    api_fragment_1 = APIFragment(block_uuid=str(blocks[0].uuid), start=0, size=5)
    api_fragment_2 = APIFragment(block_uuid=str(blocks[0].uuid), start=5, size=99999)
    _api_allocation = APIAllocation(fragments=[api_fragment_1, api_fragment_2])
    with pytest.raises(InvalidPSRDIndex):
        _allocation = Allocation.from_api(_api_allocation, pool)
    assert pool.nr_used_bytes == 0
    assert blocks[0]._data == bytes.fromhex("00010203040506070809")


def test_to_enc_str():
    """
    Create an encoded string from an Allocation.
    """
    pool, blocks = create_test_pool_and_blocks([5, 10])
    allocation = pool.allocate(8, purpose="test")
    enc_str = allocation.to_enc_str()
    assert enc_str == f"{blocks[0].uuid}:0:5,{blocks[1].uuid}:0:3"


def test_from_enc_str_success_one_fragment():
    """
    Create an allocation from a valid encoded string with one fragment.
    """
    # pylint: disable=protected-access
    pool, blocks = create_test_pool_and_blocks([10, 10])
    fragment_enc_str = f"{blocks[0].uuid}:0:5"
    allocation_enc_str = f"{fragment_enc_str}"
    allocation = Allocation.from_enc_str(allocation_enc_str, pool)
    assert len(allocation.fragments) == 1
    fragment = allocation.fragments[0]
    assert fragment.block == blocks[0]
    assert fragment.start == 0
    assert fragment.size == 5
    assert fragment.data == bytes.fromhex("0001020304")
    assert pool.nr_used_bytes == 5
    assert blocks[0]._data == bytes.fromhex("00000000000506070809")
    assert blocks[1]._data == bytes.fromhex("00010203040506070809")


def test_from_enc_str_success_two_fragments():
    """
    Create an allocation from a valid encoded string with two fragment.
    """
    # pylint: disable=protected-access
    pool, blocks = create_test_pool_and_blocks([10, 10])
    fragment_1_enc_str = f"{blocks[0].uuid}:0:10"
    fragment_2_enc_str = f"{blocks[1].uuid}:0:3"
    allocation_enc_str = f"{fragment_1_enc_str},{fragment_2_enc_str}"
    allocation = Allocation.from_enc_str(allocation_enc_str, pool)
    assert len(allocation.fragments) == 2
    fragment_1 = allocation.fragments[0]
    fragment_2 = allocation.fragments[1]
    assert fragment_1.block == blocks[0]
    assert fragment_1.start == 0
    assert fragment_1.size == 10
    assert fragment_1.data == bytes.fromhex("00010203040506070809")
    assert fragment_2.block == blocks[1]
    assert fragment_2.start == 0
    assert fragment_2.size == 3
    assert fragment_2.data == bytes.fromhex("000102")
    assert pool.nr_used_bytes == 13
    assert blocks[0]._data == bytes.fromhex("00000000000000000000")
    assert blocks[1]._data == bytes.fromhex("00000003040506070809")


def test_from_enc_str_bad_no_fragments():
    """
    Attempt to create an Allocation from a bad encoded string (no fragments).
    """
    pool, _blocks = create_test_pool_and_blocks([10])
    with pytest.raises(InvalidEncodedFragment):
        _allocation = Allocation.from_enc_str("", pool)


def test_from_enc_str_bad_fragment():
    """
    Attempt to create an Allocation from a bad APIAllocation: one of the fragments has an invalid
    block UUID.
    """
    pool, blocks = create_test_pool_and_blocks([10])
    # Bad block UUID
    with pytest.raises(InvalidBlockUUIDError):
        _allocation = Allocation.from_enc_str(f"not-a-uuid:0:5", pool)
    # Bad start index
    with pytest.raises(InvalidPSRDIndex):
        _allocation = Allocation.from_enc_str(f"{blocks[0].uuid}:20:5", pool)
    # Bad size
    with pytest.raises(InvalidPSRDIndex):
        _allocation = Allocation.from_enc_str(f"{blocks[0].uuid}:3:99999", pool)
