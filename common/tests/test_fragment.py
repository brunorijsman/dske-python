"""
Unit tests for the Fragment class.
"""

from uuid import uuid4
import pytest
from common.block import Block
from common.exceptions import InvalidBlockUUIDError, InvalidEncodedFragment
from common.fragment import APIFragment, Fragment
from common.pool import Pool
from common.utils import bytes_to_str


def _bytes_test_pattern(size):
    return bytes([i % 255 for i in range(size)])


def _create_test_block(size):
    uuid = uuid4()
    data = _bytes_test_pattern(size)
    block = Block(uuid, data)
    return block


def _create_test_pool_and_block(block_size):
    pool = Pool(name="test_pool", owner=Pool.Owner.LOCAL)
    block = _create_test_block(block_size)
    pool.add_block(block)
    return (pool, block)


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


def test_to_api():
    """
    Create an APIFragment for a Fragment.
    """
    block = _create_test_block(10)
    fragment = Fragment.allocate(block, 5)
    api_fragment = fragment.to_api()
    assert api_fragment.block_uuid == str(block.uuid)
    assert api_fragment.start == 0
    assert api_fragment.size == 5


def test_from_api_success():
    """
    Create a Fragment from a valid APIFragment.
    """
    # pylint: disable=protected-access
    (pool, block) = _create_test_pool_and_block(10)
    api_fragment = APIFragment(block_uuid=str(block.uuid), start=0, size=5)
    fragment = Fragment.from_api(api_fragment, pool)
    assert fragment.block == block
    assert fragment.start == 0
    assert fragment.size == 5
    assert fragment.data == bytes.fromhex("0001020304")
    assert block.nr_used_bytes == 5
    assert block._data == bytes.fromhex("00000000000506070809")


def test_from_api_bad_block_uuid():
    """
    Attempt to create a Fragment from a bad APIFragment (invalid block UUID).
    """
    # pylint: disable=protected-access
    (pool, _block) = _create_test_pool_and_block(10)
    # UUID string is not correctly formatted
    api_fragment = APIFragment(block_uuid="not-a-uuid", start=0, size=5)
    with pytest.raises(InvalidBlockUUIDError):
        _fragment = Fragment.from_api(api_fragment, pool)
    # UUID string is correctly formatted, but not the UUID of any block in the pool
    uuid = uuid4()
    api_fragment = APIFragment(block_uuid=str(uuid), start=0, size=5)
    with pytest.raises(InvalidBlockUUIDError):
        _fragment = Fragment.from_api(api_fragment, pool)


def test_to_enc_str():
    """
    Create an APIFragment for an encoded string.
    """
    block = _create_test_block(10)
    fragment = Fragment.allocate(block, 5)
    enc_str = fragment.to_enc_str()
    assert enc_str == f"{block.uuid}:0:5"


def test_from_enc_str_success():
    """
    Create a Fragment from a valid encoded string.
    """
    # pylint: disable=protected-access
    (pool, block) = _create_test_pool_and_block(10)
    enc_str = f"{block.uuid}:0:5"
    fragment = Fragment.from_enc_str(enc_str, pool)
    assert fragment.block == block
    assert fragment.start == 0
    assert fragment.size == 5
    assert fragment.data == bytes.fromhex("0001020304")
    assert block.nr_used_bytes == 5
    assert block._data == bytes.fromhex("00000000000506070809")


def test_from_enc_str_bad_str():
    """
    Attempt to create a Fragment from a bad encoded string (invalid encoded string format).
    """
    # pylint: disable=protected-access
    (pool, block) = _create_test_pool_and_block(10)
    # No colons
    with pytest.raises(InvalidEncodedFragment):
        _fragment = Fragment.from_enc_str("not-an-encoded-str", pool)
    # Only one colon
    with pytest.raises(InvalidEncodedFragment):
        _fragment = Fragment.from_enc_str(f"{block.uuid}:only-one-colon", pool)
    # Start is not a number
    with pytest.raises(InvalidEncodedFragment):
        _fragment = Fragment.from_enc_str(f"{block.uuid}:not-a-number:5", pool)
    # Size is not a number
    with pytest.raises(InvalidEncodedFragment):
        _fragment = Fragment.from_enc_str(f"{block.uuid}:0:not-a-number", pool)


def test_from_enc_str_bad_block_uuid():
    """
    Attempt to create a Fragment from a bad encoded string (invalid block UUID).
    """
    # pylint: disable=protected-access
    (pool, _block) = _create_test_pool_and_block(10)
    # UUID string is not correctly formatted
    enc_str = "not-a-uuid:0:5"
    with pytest.raises(InvalidBlockUUIDError):
        _fragment = Fragment.from_enc_str(enc_str, pool)
    # UUID string is correctly formatted, but not the UUID of any block in the pool
    uuid = uuid4()
    enc_str = f"{uuid}:0:5"
    with pytest.raises(InvalidBlockUUIDError):
        _fragment = Fragment.from_enc_str(enc_str, pool)
