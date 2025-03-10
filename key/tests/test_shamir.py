"""
Unit tests for Shamir Secret Sharing (implemented in PyCryptodome)
"""

import os

import shamir

# pylint: disable=missing-function-docstring


def test_shamir_secret_sharing():
    secret_size = 40  # An unusual size on purpose
    n = 5
    k = 3
    secret = os.urandom(secret_size)
    print(f"{secret=}")
    shares = shamir.make_random_shares(secret, minimum=k, shares=n)
    print(f"{shares=}")

    # shares = Shamir.split(k, n, secret)
    # print(f"{shares=}")
