# Distributed Symmetric Key Establishment (DSKE) protocol

This section describes the Distributed Symmetric Key Establishment (DSKE) protocol implemented in
this repository.

## IETF draft

The DSKE protocol implementation in this repository is based on on IETF draft
[draft-mwag-dske-02](https://datatracker.ietf.org/doc/draft-mwag-dske/02/).
Our code generally follows the high-level description in the draft, although we deviate from the
draft in certain aspects
(see
[this list of deviations](#differences-between-the-ietf-draft-and-this-implementation)
for details).

## Network topology

The following figure shows a typical example network topology:

![Example network topology](/docs/figures/topology.png)

The topology contains the following types of nodes:
* Clients.
* Hubs.
* Encryptors.

### Clients

The DSKE client nodes, or just clients for short, are represented by blue squares in the topology
diagram above.
Standard
[IETF ETSI QKD 014](https://www.etsi.org/deliver/etsi_gs/QKD/001_099/014/01.01.01_60/gs_qkd014v010101p.pdf)
uses the term Key Management Entity (KME) instead of client.

There are five clients in our example: Carol, Celia, Cindy, Conny, and Curtis.

The clients are responsible for:

1. Registering themselves with hubs.

2. Requesting Pre-Shared Random Data (PSRD) from hubs when needed.

3. Establishing keys and delivering those keys to encryptors upon request.

4. Splitting keys into key shares and relaying those keys shares from client to client through a set
   of hubs.

In our example scenario, clients Carol and Conny are responsible for producing an encryption key
and for delivering this key to encryptors Patrick and Porter respectively.
The other clients are faded out because they play no role in our example.

The key is produced using the DSKE protocol, which runs between clients and hubs.
This DSKE protocol is described in detail in section TODO below.

### Hubs

The the DSKE hub nodes, or just hubs for short, are represented by blue circles in the topology
diagram above.
IETF draft
[draft-mwag-dske-02](https://datatracker.ietf.org/doc/draft-mwag-dske/02/)
uses the term security hub.

There are five hubs in our example: Hank, Helen, Hilary, Holly, and Hugo.

The hubs are responsible for:

1. Allowing clients to register themselves with the hubs.

2. Distributing Pre-Shared Random Data (PSRD) to clients upon request.

3. Relaying key shares from client to client (we explain what key shares are later).

In our example, all five hubs are involved in relaying the key shares between clients Carol and
Conny.

### Encryptors

The encryptors are the devices that consume the keys that are produced by the clients and use them
to encrypt user traffic that is sent through a encrypted connection.
[IETF ETSI QKD 014](https://www.etsi.org/deliver/etsi_gs/QKD/001_099/014/01.01.01_60/gs_qkd014v010101p.pdf)
uses the term Secure Application Entity (SAE) instead of encryptor.

Examples of encryptors include:
* Optical encryptors, such as
  [Ciena WaveLogic](https://www.ciena.com/solutions/data-security-and-encryption).
* [MACsec](https://en.wikipedia.org/wiki/IEEE_802.1AE) encryptors, such as
  [Juniper QFX switches](https://www.juniper.net/us/en/products/switches/qfx-series.html).
* [IPsec](https://en.wikipedia.org/wiki/IPsec) encryptors, such as
  [FortiNet FortiGate Next-Generation Firewalls](https://www.fortinet.com/products/next-generation-firewall).
* [TLS](https://en.wikipedia.org/wiki/Transport_Layer_Security) /
  [SSL](https://en.wikipedia.org/wiki/Secure_Sockets_Layer) encryptors, such as
  [F5 NGINX](https://www.f5.com/company/blog/nginx/nginx-ssl).

There are two encryptors in our example: Patrick and Porter.

The encryptors are responsible for:

1. Requesting an encryption key from the clients (they may periodically request a fresh key for
   key roll-overs).

2. Use that encryption key to encrypt the user data that is sent over the encrypted connection.

When a key is established for a particular encrypted connection (e.g. an IPsec tunnel),
one side (encryptor and client) acts in the initiator role (also known as master) and the
other side acts in the role of responder (also known as slave):

1. The initiator side initiates the key establishment.
   The initiator encryptor invokes a "Get Key" API call on the initiator client to request a new
   key. It gets back a (secret) key and a (non-secret) key identifier (key ID) which uniquely
   identifies the key.

2. The initiator encryptor somehow relays the key ID to the responder encryptor.
   How this happens exactly depends on which encryption protocol is used.
   For example, IPsec uses a mechanism that is described in
   [RFC8784](https://datatracker.ietf.org/doc/html/rfc8784)
   (see
   [this blog](https://hikingandcoding.com/2024/07/16/how-to-configure-an-ipsec-tunnel-using-qkd-keys/)
   for details.)

3. When the responder encryptor receives the key ID, it invokes a "Get Key with Key ID" API call
   on the responder client to request the secret key value for that key.

4. At this point, both the initiator encryptor and the responder encryptor have the same symmetric
   secret key value and start encrypting the user data using some negotiated symmetric encryption
   protocol, such as 
   [AES](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard).

### Connectivity

The topology diagram above contains lines that represent the connectivity between the various
network nodes (clients, hubs, encryptors).
These lines are not intended to represent single-hop point-to-point connections.
Instead they represent potentially multi-hop IP connectivity between the network nodes; each link
may contain multiple switch or router hops.

## Interfaces

The topology contains the following software interfaces:
* DSKE interface.
* Key delivery interface.
* Management interface.

### DSKE interface

The DSKE interface is the interface between the clients and the hubs.
The clients and hubs run the DSKE protocol over this interface, which is described in detail
[below](#dske-protocol).
Using the DSKE protocol, the clients and the hubs collaborate with each other to establish the keys.
As mentioned before, the code in this repository implements the DSKE protocol that is defined in 
IETF draft
[draft-mwag-dske-02](https://datatracker.ietf.org/doc/draft-mwag-dske/02/).

### Key delivery interface

The key delivery interface the the interface between the clients and the encryptors.
The encryptors use the key delivery interface to retrieve keys from the clients.

There are two standard key delivery protocols:

1. [ETSI QKD 014](https://www.etsi.org/deliver/etsi_gs/QKD/001_099/014/01.01.01_60/gs_qkd014v010101p.pdf)
   is standardized by
   [ETSI](https://www.etsi.org/).
   This protocol is supported by multiple encryptor devices from different vendors.

2. The Secure Key Integration Protocol (SKIP) is defined in IETF draft
   [IETF draft draft-cisco-skip](https://datatracker.ietf.org/doc/draft-cisco-skip).
   This protocol is supported by some Cisco encryptors.

The code in this repository uses a simplified implementation of ETSI QKD 014.
(The point of this repository is not to have a full-blown implementation of ETSI QKD 014 but
rather to implement the DSKE protocol.)

### Management interface

This repository contains a management script (`manager.py`) that is used to control the network
nodes.
It can start nodes, stop nodes, report the status of nodes, and request keys.
See [the user guide](/docs/user-guide.md) for full documentation.
The clients and the hubs expose a management interface, which is a REST API, to interact with the
management script.

## Shamir's Secret Sharing (SSS)

Before we describe the DSKE protocol, we first describe
[Shamir's Secret Sharing (SSS)](https://en.wikipedia.org/wiki/Shamir%27s_secret_sharing)
algorithm, which is an essential component in the DSKE protocol.

Shamir's Secret Sharing allows a secret to be split up into some number (_n_) parts.
Each part is called a share of the secret.
The original secret can be reconstructed if you have at least _k_ out of the original _n_ shares
(were _k_ is some number smaller than _n_).
If you have fewer than _k_ shares, no information about the secret can be extracted.

In the DSKE protocol, the key that is established for the encryptors is the secret.
The key is split up into_n_ key shares, where _n_ is the number of hubs.
Each key share is relayed from the initiator client to the responder client through a different hub.

As a result of this arrangement:
1. An attacker needs to compromise at least _k_ hubs to recover the key.
2. The protocol is resilient against failures or denial-of-service attacks as long as at least
   _k_ hubs survive.

## DSKE protocol

### Out-of-band versus 

$$$

In this section we describe the differences between the DSKE protocol as specified in
[draft-mwag-dske-02](https://datatracker.ietf.org/doc/draft-mwag-dske/02/)



### Client onboarding

The following ladder diagram shows the onboarding of a new client in the network:

![Client onboarding](/docs/figures/ladder-diagram-startup.png)

The 

The steps for onboarding a new client into the network are as follows:

1. The client registers 

2.



### Key establishment

The following ladder diagram shows the establishment of a new key:

![Key establishment](/docs/figures/ladder-diagram-get-key.png)

The main responsibilities of the clients in the DSKE protocol are:

1. Each client registers itself with all hubs in the network.

2. Each client receives a large pool of Pre-Shared Random Data (PSRD) from each hub in the network.

3. The two clients involved in the key establishment (Carol and Conny in this example) run
   the DSKE protocol with all of the hubs to produce the key.
   One of the clients (Carol) is the initiator and the other client (Conny) is the responder.

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



### Placeholders

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

## Differences between the IETF draft and this implementation

In this section we describe the differences between the DSKE protocol as specified in
[draft-mwag-dske-02](https://datatracker.ietf.org/doc/draft-mwag-dske/02/)
and the DSKE protocol as implemented in this repository.

### REST message encoding

The IETF draft describes the DSKE protocol only at a high level of abstraction and does specify the
message encoding.
We had to choose some encoding of the messages ourselves.
For educational reasons, we chose implement the protocol as a set of
[REST](https://en.wikipedia.org/wiki/REST)
interfaces and use
[HTTP](https://en.wikipedia.org/wiki/HTTP)
to encode the messages.

Since the draft doesn't specify any particular encoding, using REST and HTTP is not a deviation
from the draft per-se, but in a private email exchange one of the authors of the draft told us
that he does not consider HTTP a good choice for the the DSKE protocol encoding and would prefer a
lighter-weight binary encoding.

### Client ID

The IETF draft calls for the hubs to assign a locally significant ID to the client upon
registration.
Our code doesn't to this.
Instead, clients are identified by their name which is unique within the scope of the entire
network.

## Future enhancements

In this section we list some potential future enhancements to the DSKE protocol.

### Clients register with a subset of the hubs

In our current implementation and also in the IETF draft, it is required that the client registers
itself with _all_ of the hubs in the network when the client is onboarded.
As the network grows and the number of hubs becomes very large and dynamic, this may become a
problem.
In the future, it would be useful to enhance the protocol so that a client can register itself with
only a subset of the hubs.
This, however, introduces another challenge:
when two clients want to establish a key, they have to agree on a set of hubs that they have in
common that can act as relays.
Or, alternatively, a mechanism could be introduced to do multi-hop relaying of key shares across
a series of multiple hubs.
