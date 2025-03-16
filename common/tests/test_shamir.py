"""
Unit tests for Shamir Secret Sharing.
"""

from os import urandom
from random import sample
from common import (
    reconstruct_binary_secret_from_shares,
    split_binary_secret_into_shares,
)


def shamir_split_reconstruct_scenario(size: int, nr_shares: int, min_shares: int):
    """
    Test splitting a randomly generated secret if `size` bytes into `nr_shares` shares, and then
    reconstructing the secret using a randomly selected subset of `min_shares` out of the original
    `nr_shares` shares.
    """
    info = f"size={size} nr_shares={nr_shares} min_shares={min_shares}"
    secret = urandom(size)
    shares = split_binary_secret_into_shares(secret, nr_shares, min_shares)
    assert len(shares) == nr_shares, info
    selected_shares = sample(shares, min_shares)
    reconstructed_secret = reconstruct_binary_secret_from_shares(selected_shares)
    assert secret == reconstructed_secret, info


def test_shamir_split_reconstruct_all_scenarios():
    """
    Test splitting and reconstructing secrets of various sizes, with various numbers of shares and
    minimum shares required for reconstruction.
    """
    for size in [16, 32, 1, 1000]:
        for nr_shares, min_shares in [
            (3, 3),
            (5, 5),
            (5, 3),
            (5, 1),
            (10, 10),
            (10, 3),
        ]:
            shamir_split_reconstruct_scenario(size, nr_shares, min_shares)
