# Distributed Symmetric Key Establishment (DSKE) protocol

This section describes the Distributed Symmetric Key Establishment (DSKE) protocol implemented in
this repository.

## IETF draft

The DSKE protocol implementation in this repository is based on on IETF draft
[draft-mwag-dske-02](https://datatracker.ietf.org/doc/draft-mwag-dske/02/).
This draft describes the DSKE protocol at a high level of abstraction but does **not** contain a
detailed description of the message encoding.
Our code generally follows the high-level description in the draft, although we deviate from the
draft in certain aspects (see TODO for a list of deviations).
For educational reasons, we chose implement the protocol as a set of
[REST](https://en.wikipedia.org/wiki/REST)
interfaces and use
[HTTP](https://en.wikipedia.org/wiki/HTTP)
to encode the messages.
One of the authors of the draft told us he does not consider HTTP a good choice for the the DSKE
protocol encoding and would prefer a lighter-weight binary encoding.

## Network topology

The following figure shows typical example network topology:

TODO: Add figure

The topology contains the following types of nodes:
* Clients.
* Hubs.
* Encryptors.

### Clients

The DSKE client nodes, or simply clients for short, are responsible for producing encryption keys
and for delivering the produced keys to encryptors.

In the topology diagram above the clients are represented by blue squares.
There are five clients: Carol, Celia, Cindy, Conny, and Curtis.

In our example scenario, clients Carol and Conny are responsible for producing an encryption key
and for delivering this key to encryptors Patrick and Porter respectively.
The other clients are faded out because they play no role in our example.

The key is produced using the DSKE protocol, which runs between clients Carol and Conny
(the two clients producing a pair-wise key in our example) and _all_ of the hubs.
The DSKE protocol splits the client-to-client key into fragments, known as shares, and uses
the hubs to securely relay these shares from client to client.
This is done in such a manner that they key is security delivered from client to client even if
a subset of the hubs is compromised or disabled by an attacker.

The main responsibilities of the clients in the DSKE protocol are:

1. Each client registers itself with all hubs in the network.

2. Each client receives a large pool of Pre-Shared Random Data (PSRD) from each hub in the network.

3. Produce pairwise client-to-client encryption keys between an initiator client (Carol in our 
   example) and a responder client (Conny in our example):

   3.1. The initiator client allocates a key using locally generated random data.

   3.2. The initiator client (Carol) splits the allocated key into _N_ shares using 
        [Shamir's Secret Sharing (SSS)](https://en.wikipedia.org/wiki/Shamir%27s_secret_sharing)
        algorithm, where _N_ is the number of hubs.

   3.3. The initiator client (Carol) sends each share to a separate hub, and that hub relays the
        share to the responder client.

   3.4. When a share is sent from the initiator client to a hub or from a hub to the responder
        client, the share is one-time-pad encrypted and authenticated using a chunk of bits that
        are consumed from the Pre-Shared Random Data (PSRD) exchanged a-priori between that
        particular client and that particular hub.

   3.5. The responder client receives shares from some subset of the hubs.
        Perhaps it doesn't receive all shares from all hubs because some hubs might be compromised
        or might have failed.

   3.6. The responder client reconstructs the client-to-client key from the received shares.
        [Shamir's Secret Sharing (SSS)](https://en.wikipedia.org/wiki/Shamir%27s_secret_sharing)
        algorithm allows the client-to-client key to be reconstructed, even if some of the shares
        are missing.

This DSKE protocol is described in much more detail further below.

Carol and Conny deliver the produced key to encryptors Patrick and Porter respectively over
the key delivery interface.
The key delivery interface is also described in detail further below.

TODO: Continue from here.

### Hubs

The hubs are responsible for:

1. Allowing clients to register themselves with the hubs.

2. Distributing Pre-Shared Random Data (PSRD) to clients.

3. Producing client-to-hub key shares by allocating blocks of bits from the PSRD.

4. Relaying

### Encryptors

TODO

### Connectivity

The lines between the clients and the hubs indicate that there is IP connectivity between the
clients and the hubs.
There may be multiple IP hops between the clients and the hubs, which is not shown in the diagram.
The line is not intended to represent a direct point-to-point link

## Interfaces

The topology contains the following interfaces:
* DSKE interface.
* Key delivery interface.
* Management interface.

### DSKE interface

The DSKE interface is an interface between the clients and the hubs.

The clients and hubs run the DSKE protocol over this interface that produces the key.

### Key delivery interface

The key delivery interface is an interface between the clients and the encryptors.



### Management interface

TODO

## DSKE protocol

For now, we just summarize the main steps:

1. Prior to the production of any keys, the hubs distribute blocks of Pre-Shared Random Data (PSRD)
   to the clients using a secure out-of-band mechanism.
   The DSKE protocol produces client-to-hub shared secrets by allocating chunks of bits from this
   PSRD.

2. The hubs act as relay nodes. In our example, each hub relays the carol-to-hub shared secret
   to conny by one-time-pad encrypting it using the conny-to-hub shared secret.

3. Each hub only relays a fragment of the client-to-client key, known as a share.
   [Shamir's Secret Sharing (SSS)](https://en.wikipedia.org/wiki/Shamir%27s_secret_sharing).
   Client Carol splits the key into shares and sends those share to client Conny, using a different
   hub to relay each share.
   Client Conny reconstructs the key from received shares received from the hubs.
   Shamir's Secret Sharing algorithm has guarantees that:

   A. The hubs are not able to learn any information from the client-to-client full key from the
      single share that is relayed through them. At least _k_

   B. 

## Comparison with other key establishment protocols

DSKE provides the same functionality, namely key agreement, 

* Traditional classical protocols such as Diffie-Hellman (DH) and Elliptic Curve Diffie-Hellman
   (ECDH).

* Post-Quantum Cryptography (PQC) protocols such as the 
[Module-Lattice Key Encapsulation Mechanism (ML-KEM)](https://en.wikipedia.org/wiki/Kyber).

* Quantum Key Distribution (QKD) protocols such as 
[Bennett and Brassard 84 (BB84)](https://en.wikipedia.org/wiki/BB84).

Like ML-KEM and BB84, DSKE can resist attacks by quantum computers.

DSKE allows pairs of  to agree 
