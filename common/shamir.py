"""
Shamir Secret Sharing (SSS).
"""

# This code is based on file shamir.py in package python-shamir-mnemonic which was cloned from the
# following repository:
# https://salsa.debian.org/python-team/packages/python-shamir-mnemonic
# and then heavily modified to fit the needs of this project.
#
# The following is a copy of the license in the file LICENSE in the original package
# python-shamir-mnemonic:
#
# --- Start original python-shamir-mnemonic package license ---------------------------------------
#
# Copyright 2019 SatoshiLabs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
# OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# --- End original python-shamir-mnemonic package license -----------------------------------------
#
# The following is a copy of the license in the original file shamir.py in the original package:
#
# --- Start original shamir.py file license -------------------------------------------------------
#
# Copyright (c) 2018 Andrew R. Kozlik
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# --- End original shamir.py file license ---------------------------------------------------------


import hmac
import secrets
from typing import List, Sequence, Tuple


# The length of the digest of the shared secret in bytes.
DIGEST_LENGTH_BYTES = 4

# The minimum length of the shared secret in bytes.
MIN_KEY_LENGTH = DIGEST_LENGTH_BYTES

# The maximum number of shares that can be created.
MAX_SHARE_COUNT = 16

# The index of the share containing the shared secret.
SECRET_INDEX = 255

# The index of the share containing the digest of the shared secret.
DIGEST_INDEX = 254


# Source of random bytes. Can be overridden for deterministic testing.
RANDOM_BYTES = secrets.token_bytes


def _precompute_exp_log() -> Tuple[List[int], List[int]]:
    exp = [0 for i in range(255)]
    log = [0 for i in range(256)]
    poly = 1
    for i in range(255):
        exp[i] = poly
        log[poly] = i
        # Multiply poly by the polynomial x + 1.
        poly = (poly << 1) ^ poly
        # Reduce poly by x^8 + x^4 + x^3 + x + 1.
        if poly & 0x100:
            poly ^= 0x11B
    return exp, log


EXP_TABLE, LOG_TABLE = _precompute_exp_log()


def _interpolate(shares: Sequence[Tuple[int, bytes]], x: int) -> bytes:
    """
    Returns f(x) given the Shamir shares (x_1, f(x_1)), ... , (x_k, f(x_k)).
    """
    x_coordinates = set(share[0] for share in shares)
    if len(x_coordinates) != len(shares):
        raise ValueError("Invalid set of shares. Share indices must be unique.")
    share_value_lengths = set(len(share[1]) for share in shares)
    if len(share_value_lengths) != 1:
        raise ValueError(
            "Invalid set of shares. All share values must have the same length."
        )
    if x in x_coordinates:
        for share in shares:
            if share[0] == x:
                return share[1]
    # Logarithm of the product of (x_i - x) for i = 1, ... , k.
    log_prod = sum(LOG_TABLE[share[0] ^ x] for share in shares)
    result = bytes(share_value_lengths.pop())
    for share in shares:
        # The logarithm of the Lagrange basis polynomial evaluated at x.
        log_basis_eval = (
            log_prod
            - LOG_TABLE[share[0] ^ x]
            - sum(LOG_TABLE[share[0] ^ other[0]] for other in shares)
        ) % 255
        result = bytes(
            intermediate_sum
            ^ (
                EXP_TABLE[(LOG_TABLE[share_val] + log_basis_eval) % 255]
                if share_val != 0
                else 0
            )
            for share_val, intermediate_sum in zip(share[1], result)
        )
    return result


def _create_digest(random_data: bytes, secret: bytes) -> bytes:
    return hmac.new(random_data, secret, "sha256").digest()[:DIGEST_LENGTH_BYTES]


def split_binary_secret_into_shares(
    secret: bytes,
    nr_shares: int,
    min_nr_shares: int,
) -> list[(int, bytes)]:
    """
    Split a secret into nr_shares shares. The minimum number of shares required to
    reconstruct the secret is min_nr_shares.
    """
    if len(secret) < MIN_KEY_LENGTH:
        raise ValueError(
            f"The shared secret must be at least {MIN_KEY_LENGTH} bytes long."
        )
    if min_nr_shares < 1:
        raise ValueError("The requested min_nr_shares must be a positive integer.")
    if min_nr_shares > nr_shares:
        raise ValueError(
            "The requested min_nr_shares must not exceed the number of shares."
        )
    if nr_shares > MAX_SHARE_COUNT:
        raise ValueError(
            f"The requested number of shares must not exceed {MAX_SHARE_COUNT}."
        )
    if min_nr_shares == 1:
        # If the min_nr_shares is 1, then the digest of the secret is not used.
        return [(i, secret) for i in range(nr_shares)]
    random_share_count = min_nr_shares - 2
    shares = [(i, RANDOM_BYTES(len(secret))) for i in range(random_share_count)]
    digest_random_bytes = RANDOM_BYTES(len(secret) - DIGEST_LENGTH_BYTES)
    digest = _create_digest(digest_random_bytes, secret)
    digest_share_data = digest + digest_random_bytes
    interpolation_shares = shares + [
        (DIGEST_INDEX, digest_share_data),
        (SECRET_INDEX, secret),
    ]
    for i in range(random_share_count, nr_shares):
        shares.append((i, _interpolate(interpolation_shares, i)))
    return shares


def reconstruct_binary_secret_from_shares(
    min_nr_shares: int, shares: list[(int, bytes)]
) -> bytes:
    """
    Reconstruct a binary secret from shares.
    """
    if min_nr_shares == 1:
        first_share = next(iter(shares))
        first_share_data = first_share[1]
        return first_share_data
    secret = _interpolate(shares, SECRET_INDEX)
    digest_share = _interpolate(shares, DIGEST_INDEX)
    digest = digest_share[:DIGEST_LENGTH_BYTES]
    digest_random_bytes = digest_share[DIGEST_LENGTH_BYTES:]
    if digest != _create_digest(digest_random_bytes, secret):
        raise ValueError("Invalid digest of the shared secret.")
    return secret
