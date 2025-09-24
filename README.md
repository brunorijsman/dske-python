# Distributed Symmetric Key Establishment (DSKE)

I assume that you are aware of the fact that existing
[key exchange](https://en.wikipedia.org/wiki/Key_exchange)
protocols such as
[Diffie-Hellman (DH)](https://en.wikipedia.org/wiki/Diffie%E2%80%93Hellman_key_exchange),
[Elliptic Curve Diffie-Hellman (ECDH)](https://en.wikipedia.org/wiki/Elliptic-curve_Diffie%E2%80%93Hellman),
and
[Rivest-Shamir-Adleman (RSA)](https://en.wikipedia.org/wiki/RSA_cryptosystem)
are vulnerable to attack by future quantum computers due to the discovery of
[Shor's algorithm](https://en.wikipedia.org/wiki/Shor%27s_algorithm).

I also assume that you are familiar with
[Post-Quantum Cryptography (PQC)](https://en.wikipedia.org/wiki/Post-quantum_cryptography)
and
[Quantum Key Distribution (QKD)](https://en.wikipedia.org/wiki/Quantum_key_distribution)
which are the two prevalent quantum-safe key exchange methods.

Most people are less familiar with Distribute Symmetric Key Establishment (DSKE) which is a
completely different approach for quantum-safe key exchange.

The DSKE approach is described in IETF Internet Draft
[draft-mwag-dske](https://datatracker.ietf.org/doc/draft-mwag-dske/)
and has been commercialized by
[Quantum Bridge](https://qubridge.io/).

This repository contains an open source implementation of DSKE inspired by the IETF draft.
I say "inspired by" because the draft only describes the general approach and not a detailed
protocol and because my implementation differs from the draft on some aspects.

Documentation:

* [User guide](/docs/user-guide.md)

* [Protocol guide](/docs/protocol-guide.md)

* [Developer guide](/docs/developer-guide.md)

