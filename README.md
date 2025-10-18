# Distributed Symmetric Key Establishment (DSKE)

Currently deployed
[key exchange](https://en.wikipedia.org/wiki/Key_exchange)
protocols such as
[Diffie-Hellman (DH)](https://en.wikipedia.org/wiki/Diffie%E2%80%93Hellman_key_exchange),
[Elliptic Curve Diffie-Hellman (ECDH)](https://en.wikipedia.org/wiki/Elliptic-curve_Diffie%E2%80%93Hellman),
and
[Rivest-Shamir-Adleman (RSA)](https://en.wikipedia.org/wiki/RSA_cryptosystem)
are vulnerable to attack by future quantum computers due to the discovery of
[Shor's algorithm](https://en.wikipedia.org/wiki/Shor%27s_algorithm).

New protocols are under development to make key exchange quantum-safe.
The best-known two methods are
[Post-Quantum Cryptography (PQC)](https://en.wikipedia.org/wiki/Post-quantum_cryptography)
and
[Quantum Key Distribution (QKD)](https://en.wikipedia.org/wiki/Quantum_key_distribution).

Most people are less familiar with Distributed Symmetric Key Establishment (DSKE) which is a
completely different approach for quantum-safe key exchange.

The DSKE approach is described in IETF Internet Draft
[draft-mwag-dske](https://datatracker.ietf.org/doc/draft-mwag-dske/)
and in arXiv paper
[arXiv:2205.00615 Distributed Symmetric Key Establishment: A scalable, quantum-proof key distribution system](https://arxiv.org/abs/2205.00615).
It has been commercialized by
[Quantum Bridge](https://qubridge.io/)
(who are not involved with this open source project).

This repository contains an open source implementation of DSKE inspired by the IETF draft.
I say "inspired by" because the draft only describes the general approach and not a detailed
protocol and because my implementation differs from the draft in some aspects.

Documentation:

* [Getting started guide](/docs/getting-started-guide.md)

* [Introduction: What is DSKE and what problem does it solve?](/docs/what-is-dske-and-what-problem-does-it-solve.md)

* [Protocol guide](/docs/protocol-guide.md)

* [User guide](/docs/user-guide.md)

* [Developer guide](/docs/developer-guide.md)

