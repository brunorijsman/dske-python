# Distributed Symmetric Key Establishment (DSKE)

This repository contains an open source implementation of Distributed Symmetric Key Establishment
(DSKE).

DSKE is a key distribution protocol that allows network nodes, known as client nodes (or clients
for short), to agree on a shared secret.

This shared secret is typically used as a symmetric encryption key to to encrypt traffic between the
two nodes using some symmetric encryption protocol such as the
[Advanced Encryption Standard (AES)](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard)
or
[one-time-pad](https://en.wikipedia.org/wiki/One-time_pad).

Documentation:

* [Distributed Distributed Symmetric Key Establishment (DSKE) protocol](docs/dske-protocol.md)

* [User guide](/docs/user-guide.md)

* [Developer guide](/docs/developer-guide.md)

