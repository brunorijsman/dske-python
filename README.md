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

TODO: Put a summary of the protocol here:

Such a key is produced as follows:
- The initiator client:
  - Uses a random number generator to create the key.
  - Assigns a globally unique UUID to the key.
  - Splits the key up into shares.
  - Sends each share to a different hub using a POST key-share message.
  - The share is encrypted using key bytes allocated from the Pre-Shared Random Data (PSRD) shared
    with that hub.
  - The message is authenticated by signing it using key bytes allocated from the PSRD with that
    hub.
  - Delivers the key and the key ID to the initiator encryptor.
- ... finish this ...

