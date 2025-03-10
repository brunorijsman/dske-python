"""
The following Python implementation of Shamir's secret sharing is
released into the Public Domain under the terms of CC0 and OWFa:
https://creativecommons.org/publicdomain/zero/1.0/
http://www.openwebfoundation.org/legal/the-owf-1-0-agreements/owfa-1-0

See the bottom few lines for usage. Tested on Python 2 and 3.

Copied fom https://en.wikipedia.org/wiki/Shamir on 10-Mar-2025
Modified by Bruno Rijsman
"""

# TODO: draft-mwag-dske-01 appendix A defines the following Galois fields:
#       (1) GF(2^128) expressed in a polynomial basis modulo the irreducible polynomial
#           1 + x + x^2 + x^7 + x^128
#       (2) GF(2^8) with irreducible polynomial 1 + x + x^3 + x^4 + x^8
#       I don't yet understand what an "irreducible polynomial" is; it seems related to
#       the concept of field extensions, which I also do not yet understand.
#       For now, I use the Galois field
#       References:
#       * https://medium.com/asecuritysite-when-bob-met-alice/sage-galois-field-and-irreducible-polynomials-882bb474e1bc
#       * https://en.wikipedia.org/wiki/Finite_field#Explicit_construction
#       * https://mpyc.readthedocs.io/en/latest/mpyc.html
#       * https://gendignoux.com/blog/2021/11/01/horcrux-1-math.html
#         This one seems to be the most clear from a programmer's perspective; but it is Rust
#       * https://github.com/adviksinghania/shamir-secret-sharing
#       * https://github.com/NitishGadangi/shamir-secret-sharing-POC
#         This one is in Python and uses GF(256)
#         Uses this library https://gf256.readthedocs.io/en/stable/ for GF(256) operations
#
# If you search the gf256 source code for "irreducible", you will find that it uses
# polynomial 0b100011011, which is 1 + x + x^3 + x^4 + x^8
# This is the same polynomial as in draft-mwag-dske-01 appendix A
# This polynomial is also used in the AES algorithm
#
# We shall use this library for GF(256) operations

from __future__ import division
from __future__ import print_function

import random
import functools

# 12th Mersenne Prime
_PRIME = 2**127 - 1

_RINT = functools.partial(random.SystemRandom().randint, 0)


def _eval_at(poly, x, prime):
    """Evaluates polynomial (coefficient tuple) at x, used to generate a
    shamir pool in make_random_shares below.
    """
    print(f"{poly=}")
    accum = 0
    for coeff in reversed(poly):
        accum *= x
        print(f"{accum=}")
        print(f"{coeff=}")
        accum += coeff
        accum %= prime
    return accum


def _all_unique(lst):
    """
    Are all elements of a list unique?
    """
    return len(lst) == len(set(lst))


def make_random_shares(secret, minimum, shares, prime=_PRIME):
    """
    Generates a random shamir pool for a given secret, returns share points.
    """
    if minimum > shares:
        raise ValueError("Pool secret would be irrecoverable.")
    while True:
        poly = [secret] + [_RINT(prime - 1) for i in range(minimum - 1)]
        if _all_unique(poly):
            break
    points = [(i, _eval_at(poly, i, prime)) for i in range(1, shares + 1)]
    return points


def _extended_gcd(a, b):
    """
    Division in integers modulus p means finding the inverse of the
    denominator modulo p and then multiplying the numerator by this
    inverse (Note: inverse of A is B such that A*B % p == 1). This can
    be computed via the extended Euclidean algorithm
    http://en.wikipedia.org/wiki/Modular_multiplicative_inverse#Computation
    """
    x = 0
    last_x = 1
    y = 1
    last_y = 0
    while b != 0:
        quot = a // b
        a, b = b, a % b
        x, last_x = last_x - quot * x, x
        y, last_y = last_y - quot * y, y
    return last_x, last_y


def _divmod(num, den, p):
    """Compute num / den modulo prime p

    To explain this, the result will be such that:
    den * _divmod(num, den, p) % p == num
    """
    inv, _ = _extended_gcd(den, p)
    return num * inv


def _product_of_inputs(vals):
    """
    Product of values in a list.
    """
    accum = 1
    for v in vals:
        accum *= v
    return accum


def _lagrange_interpolate(x, x_s, y_s, p):
    """
    Find the y-value for the given x, given n (x, y) points;
    k points will define a polynomial of up to kth order.
    """
    k = len(x_s)
    assert k == len(set(x_s)), "points must be distinct"

    nums = []  # avoid inexact division
    dens = []
    for i in range(k):
        others = list(x_s)
        cur = others.pop(i)
        nums.append(_product_of_inputs(x - o for o in others))
        dens.append(_product_of_inputs(cur - o for o in others))
    den = _product_of_inputs(dens)
    num = sum(_divmod(nums[i] * den * y_s[i] % p, dens[i], p) for i in range(k))
    return (_divmod(num, den, p) + p) % p


def recover_secret(shares, prime=_PRIME):
    """
    Recover the secret from share points
    (points (x,y) on the polynomial).
    """
    if len(shares) < 3:
        raise ValueError("need at least three shares")
    x_s, y_s = zip(*shares)
    return _lagrange_interpolate(0, x_s, y_s, prime)


# TODO: Remove the main function


def main():
    """Main function"""
    secret = 1234
    shares = make_random_shares(secret, minimum=3, shares=6)

    print("Secret:                                                     ", secret)
    print("Shares:")
    if shares:
        for share in shares:
            print("  ", share)

    print(
        "Secret recovered from minimum subset of shares:             ",
        recover_secret(shares[:3]),
    )
    print(
        "Secret recovered from a different minimum subset of shares: ",
        recover_secret(shares[-3:]),
    )


if __name__ == "__main__":
    main()
