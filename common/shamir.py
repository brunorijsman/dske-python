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

# import secrets
# from dataclasses import dataclass

import hmac
import secrets  # TODO: Use secrets everywhere instead of os.urandom
from typing import List, NamedTuple, Sequence, Tuple

# from . import cipher
# from .constants import (
#     DIGEST_INDEX,
#     DIGEST_LENGTH_BYTES,
#     GROUP_PREFIX_LENGTH_WORDS,
#     ID_EXP_LENGTH_WORDS,
#     ID_LENGTH_BITS,
#     MAX_SHARE_COUNT,
#     MIN_STRENGTH_BITS,
#     SECRET_INDEX,
# )
# from .share import Share, ShareCommonParameters, ShareGroupParameters
# from .utils import MnemonicError, bits_to_bytes

# TODO: Remove this
# pylint: disable=missing-function-docstring,missing-class-docstring


DIGEST_LENGTH_BYTES = 4
"""The length of the digest of the shared secret in bytes."""

MAX_SHARE_COUNT = 16
"""The maximum number of shares that can be created."""

SECRET_INDEX = 255
"""The index of the share containing the shared secret."""

DIGEST_INDEX = 254
"""The index of the share containing the digest of the shared secret."""


class RawShare(NamedTuple):
    x: int
    data: bytes


# class ShareGroup:
#     def __init__(self) -> None:
#         self.shares: Set[Share] = set()

#     def __iter__(self) -> Iterator[Share]:
#         return iter(self.shares)

#     def __len__(self) -> int:
#         return len(self.shares)

#     def __bool__(self) -> bool:
#         return bool(self.shares)

#     def __contains__(self, obj: Any) -> bool:
#         return obj in self.shares

#     def add(self, share: Share) -> None:
#         if self.shares and self.group_parameters() != share.group_parameters():
#             fields = zip(
#                 ShareGroupParameters._fields,
#                 self.group_parameters(),
#                 share.group_parameters(),
#             )
#             mismatch = next(name for name, x, y in fields if x != y)
#             raise MnemonicError(
#                 f"Invalid set of mnemonics. The {mismatch} parameters don't match."
#             )

#         self.shares.add(share)

#     def to_raw_shares(self) -> List[RawShare]:
#         return [RawShare(s.index, s.value) for s in self.shares]

#     def get_minimal_group(self) -> "ShareGroup":
#         group = ShareGroup()
#         group.shares = set(
#             share for _, share in zip(range(self.member_threshold()), self.shares)
#         )
#         return group

#     def common_parameters(self) -> ShareCommonParameters:
#         return next(iter(self.shares)).common_parameters()

#     def group_parameters(self) -> ShareGroupParameters:
#         return next(iter(self.shares)).group_parameters()

#     def member_threshold(self) -> int:
#         return next(iter(self.shares)).member_threshold

#     def is_complete(self) -> bool:
#         if self.shares:
#             return len(self.shares) >= self.member_threshold()
#         else:
#             return False


# @dataclass(frozen=True)
# class EncryptedMasterSecret:
#     identifier: int
#     extendable: bool
#     iteration_exponent: int
#     ciphertext: bytes

#     @classmethod
#     def from_master_secret(
#         cls,
#         master_secret: bytes,
#         passphrase: bytes,
#         identifier: int,
#         extendable: bool,
#         iteration_exponent: int,
#     ) -> "EncryptedMasterSecret":
#         ciphertext = cipher.encrypt(
#             master_secret, passphrase, iteration_exponent, identifier, extendable
#         )
#         return EncryptedMasterSecret(
#             identifier, extendable, iteration_exponent, ciphertext
#         )

#     def decrypt(self, passphrase: bytes) -> bytes:
#         return cipher.decrypt(
#             self.ciphertext,
#             passphrase,
#             self.iteration_exponent,
#             self.identifier,
#             self.extendable,
#         )


RANDOM_BYTES = secrets.token_bytes
"""Source of random bytes. Can be overriden for deterministic testing."""


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


def _interpolate(shares: Sequence[RawShare], x: int) -> bytes:
    """
    Returns f(x) given the Shamir shares (x_1, f(x_1)), ... , (x_k, f(x_k)).
    :param shares: The Shamir shares.
    :type shares: A list of pairs (x_i, y_i), where x_i is an integer and y_i is an array of
        bytes representing the evaluations of the polynomials in x_i.
    :param int x: The x coordinate of the result.
    :return: Evaluations of the polynomials in x.
    :rtype: Array of bytes.
    """

    x_coordinates = set(share.x for share in shares)

    if len(x_coordinates) != len(shares):
        raise ValueError("Invalid set of shares. Share indices must be unique.")

    share_value_lengths = set(len(share.data) for share in shares)
    if len(share_value_lengths) != 1:
        raise ValueError(
            "Invalid set of shares. All share values must have the same length."
        )

    if x in x_coordinates:
        for share in shares:
            if share.x == x:
                return share.data

    # Logarithm of the product of (x_i - x) for i = 1, ... , k.
    log_prod = sum(LOG_TABLE[share.x ^ x] for share in shares)

    result = bytes(share_value_lengths.pop())
    for share in shares:
        # The logarithm of the Lagrange basis polynomial evaluated at x.
        log_basis_eval = (
            log_prod
            - LOG_TABLE[share.x ^ x]
            - sum(LOG_TABLE[share.x ^ other.x] for other in shares)
        ) % 255

        result = bytes(
            intermediate_sum
            ^ (
                EXP_TABLE[(LOG_TABLE[share_val] + log_basis_eval) % 255]
                if share_val != 0
                else 0
            )
            for share_val, intermediate_sum in zip(share.data, result)
        )

    return result


def _create_digest(random_data: bytes, shared_secret: bytes) -> bytes:
    return hmac.new(random_data, shared_secret, "sha256").digest()[:DIGEST_LENGTH_BYTES]


def _split_secret(
    threshold: int, share_count: int, shared_secret: bytes
) -> List[RawShare]:
    if threshold < 1:
        raise ValueError("The requested threshold must be a positive integer.")

    if threshold > share_count:
        raise ValueError(
            "The requested threshold must not exceed the number of shares."
        )

    if share_count > MAX_SHARE_COUNT:
        raise ValueError(
            f"The requested number of shares must not exceed {MAX_SHARE_COUNT}."
        )

    # TODO: We won't allow a threshold of 1; we will require at least 2 (or even 3?)
    # If the threshold is 1, then the digest of the shared secret is not used.
    if threshold == 1:
        return [RawShare(i, shared_secret) for i in range(share_count)]

    random_share_count = threshold - 2

    shares = [
        RawShare(i, RANDOM_BYTES(len(shared_secret))) for i in range(random_share_count)
    ]

    random_part = RANDOM_BYTES(len(shared_secret) - DIGEST_LENGTH_BYTES)
    digest = _create_digest(random_part, shared_secret)

    base_shares = shares + [
        RawShare(DIGEST_INDEX, digest + random_part),
        RawShare(SECRET_INDEX, shared_secret),
    ]

    for i in range(random_share_count, share_count):
        shares.append(RawShare(i, _interpolate(base_shares, i)))

    return shares


def _recover_secret(threshold: int, shares: Sequence[RawShare]) -> bytes:
    # If the threshold is 1, then the digest of the shared secret is not used.
    if threshold == 1:
        return next(iter(shares)).data

    shared_secret = _interpolate(shares, SECRET_INDEX)
    digest_share = _interpolate(shares, DIGEST_INDEX)
    digest = digest_share[:DIGEST_LENGTH_BYTES]
    random_part = digest_share[DIGEST_LENGTH_BYTES:]

    if digest != _create_digest(random_part, shared_secret):
        raise ValueError("Invalid digest of the shared secret.")

    return shared_secret


# def decode_mnemonics(mnemonics: Iterable[str]) -> Dict[int, ShareGroup]:
#     common_params: Set[ShareCommonParameters] = set()
#     groups: Dict[int, ShareGroup] = {}
#     for mnemonic in mnemonics:
#         share = Share.from_mnemonic(mnemonic)
#         common_params.add(share.common_parameters())
#         group = groups.setdefault(share.group_index, ShareGroup())
#         group.add(share)

#     if len(common_params) != 1:
#         raise MnemonicError(
#             "Invalid set of mnemonics. "
#             f"All mnemonics must begin with the same {ID_EXP_LENGTH_WORDS} words, "
#             "must have the same group threshold and the same group count."
#         )

#     return groups


# def split_ems(
#     group_threshold: int,
#     groups: Sequence[Tuple[int, int]],
#     encrypted_master_secret: EncryptedMasterSecret,
# ) -> List[List[Share]]:
#     """
#     Split an Encrypted Master Secret into mnemonic shares.

#     This function is a counterpart to `recover_ems`, and it is used as a subroutine in
#     `generate_mnemonics`. The input is an *already encrypted* Master Secret (EMS), so it
#     is possible to encrypt the Master Secret in advance and perform the splitting later.

#     :param group_threshold: The number of groups required to reconstruct the master secret.
#     :param groups: A list of (member_threshold, member_count) pairs for each group, where member_count
#         is the number of shares to generate for the group and member_threshold is the number of members required to
#         reconstruct the group secret.
#     :param encrypted_master_secret: The encrypted master secret to split.
#     :return: List of groups of mnemonics.
#     """
#     if len(encrypted_master_secret.ciphertext) * 8 < MIN_STRENGTH_BITS:
#         raise ValueError(
#             "The length of the master secret must be "
#             f"at least {bits_to_bytes(MIN_STRENGTH_BITS)} bytes."
#         )

#     if group_threshold > len(groups):
#         raise ValueError(
#             "The requested group threshold must not exceed the number of groups."
#         )

#     if any(
#         member_threshold == 1 and member_count > 1
#         for member_threshold, member_count in groups
#     ):
#         raise ValueError(
#             "Creating multiple member shares with member threshold 1 is not allowed. "
#             "Use 1-of-1 member sharing instead."
#         )

#     group_shares = _split_secret(
#         group_threshold, len(groups), encrypted_master_secret.ciphertext
#     )

#     # TODO: At this point group_shares is a list of RawShare objects.


# def _random_identifier() -> int:
#     """Returns a random identifier with the given bit length."""
#     identifier = int.from_bytes(RANDOM_BYTES(bits_to_bytes(ID_LENGTH_BITS)), "big")
#     return identifier & ((1 << ID_LENGTH_BITS) - 1)


# def generate_mnemonics(
#     group_threshold: int,
#     groups: Sequence[Tuple[int, int]],
#     master_secret: bytes,
#     passphrase: bytes = b"",
#     extendable: bool = True,
#     iteration_exponent: int = 1,
# ) -> List[List[str]]:
#     """
#     Split a master secret into mnemonic shares using Shamir's secret sharing scheme.

#     The supplied Master Secret is encrypted by the passphrase (empty passphrase is used
#     if none is provided) and split into a set of mnemonic shares.

#     This is the user-friendly method to back up a pre-existing secret with the Shamir
#     scheme, optionally protected by a passphrase.

#     :param group_threshold: The number of groups required to reconstruct the master secret.
#     :param groups: A list of (member_threshold, member_count) pairs for each group, where member_count
#         is the number of shares to generate for the group and member_threshold is the number of members required to
#         reconstruct the group secret.
#     :param master_secret: The master secret to split.
#     :param passphrase: The passphrase used to encrypt the master secret.
#     :param int iteration_exponent: The encryption iteration exponent.
#     :return: List of groups mnemonics.
#     """
#     if not all(32 <= c <= 126 for c in passphrase):
#         raise ValueError(
#             "The passphrase must contain only printable ASCII characters (code points 32-126)."
#         )

#     identifier = _random_identifier()
#     encrypted_master_secret = EncryptedMasterSecret.from_master_secret(
#         master_secret, passphrase, identifier, extendable, iteration_exponent
#     )
#     grouped_shares = split_ems(group_threshold, groups, encrypted_master_secret)
#     return [[share.mnemonic() for share in group] for group in grouped_shares]


# def recover_ems(groups: Dict[int, ShareGroup]) -> EncryptedMasterSecret:
#     """
#     Combine shares, recover metadata and the Encrypted Master Secret.

#     This function is a counterpart to `split_ems`, and it is used as a subroutine in
#     `combine_mnemonics`. It returns the EMS itself and data required for its decryption,
#     except for the passphrase. It is thus possible to defer decryption of the Master
#     Secret to a later time.

#     :param groups: Set of shares classified into groups.
#     :return: Encrypted Master Secret
#     """

#     if not groups:
#         raise MnemonicError("The set of shares is empty.")

#     params = next(iter(groups.values())).common_parameters()

#     if len(groups) < params.group_threshold:
#         raise MnemonicError(
#             "Insufficient number of mnemonic groups. "
#             f"The required number of groups is {params.group_threshold}."
#         )

#     if len(groups) != params.group_threshold:
#         raise MnemonicError(
#             "Wrong number of mnemonic groups. "
#             f"Expected {params.group_threshold} groups, "
#             f"but {len(groups)} were provided."
#         )

#     for group in groups.values():
#         if len(group) != group.member_threshold():
#             share_words = next(iter(group)).words()
#             prefix = " ".join(share_words[:GROUP_PREFIX_LENGTH_WORDS])
#             raise MnemonicError(
#                 "Wrong number of mnemonics. "
#                 f'Expected {group.member_threshold()} mnemonics starting with "{prefix} ...", '
#                 f"but {len(group)} were provided."
#             )

#     group_shares = [
#         RawShare(
#             group_index,
#             _recover_secret(group.member_threshold(), group.to_raw_shares()),
#         )
#         for group_index, group in groups.items()
#     ]

#     ciphertext = _recover_secret(params.group_threshold, group_shares)
#     return EncryptedMasterSecret(
#         params.identifier, params.extendable, params.iteration_exponent, ciphertext
#     )


# def combine_mnemonics(mnemonics: Iterable[str], passphrase: bytes = b"") -> bytes:
#     """
#     Combine mnemonic shares to obtain the master secret which was previously split
#     using Shamir's secret sharing scheme.

#     This is the user-friendly method to recover a backed-up secret optionally protected
#     by a passphrase.

#     :param mnemonics: List of mnemonics.
#     :param passphrase: The passphrase used to encrypt the master secret.
#     :return: The master secret.
#     """

#     if not mnemonics:
#         raise MnemonicError("The list of mnemonics is empty.")

#     groups = decode_mnemonics(mnemonics)
#     encrypted_master_secret = recover_ems(groups)
#     return encrypted_master_secret.decrypt(passphrase)


# ---- Place holder code until real Shamir Secret Sharing is implemented --------------------------


def split_binary_secret_into_shares(
    secret: bytes,
    nr_shares: int,
    min_nr_shares: int,
) -> list[(int, bytes)]:
    """
    Split a binary secret into `nr_shares` shares. The minimum number of shares required to
    reconstruct the binary is `min_nr_shares`.
    """
    # TODO: For now, this is just a dummy implementation: each share contains a copy of the
    #       original secret. So, it's trivial to reconstruct the original secret from any single
    #       share.
    assert nr_shares >= min_nr_shares
    shares = []
    for share_index in range(nr_shares):
        share = (share_index, secret)
        shares.append(share)
    return shares


def reconstruct_binary_secret_from_shares(shares: list[(int, bytes)]) -> bytes:
    """
    Reconstruct a binary secret from shares.
    """
    # TODO: Same dummy implementation as described above.
    # TODO: Throw an exception if the secret cannot be reconstructed.
    assert len(shares) > 0
    return shares[0][1]
