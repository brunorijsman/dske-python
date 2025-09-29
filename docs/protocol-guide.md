# Protocol guide

This chapter describes the Distributed Symmetric Key Establishment (DSKE) protocol as it is
implemented in this repository.

## Inspiration

The DSKE implementation in this repository is inspired by:

* IETF Internet Draft draft-mwag-dske-02<br>
  The Distributed Symmetric Key Establishment (DSKE) Protocol.<br>
  [https://datatracker.ietf.org/doc/draft-mwag-dske/02/](https://datatracker.ietf.org/doc/draft-mwag-dske/02/)

 * Paper arXiv:2205.00615:<br>
   Distributed Symmetric Key Establishment: A scalable, quantum-proof key distribution system.<br>
   [https://arxiv.org/abs/2205.00615](https://arxiv.org/abs/2205.00615)

 * Paper arXiv:2304.13789<br>
   Composable Security of Distributed Symmetric Key Establishment Protocol.<br>
   [https://arxiv.org/abs/2304.13789](https://arxiv.org/abs/2304.13789)

I say "inspired by" because:

 * The draft and the paper only describe the general approach.
   They do not describe the protocol in sufficient detail for an unambiguous interoperable
   implementation.
   For example, the draft and the paper do not specify message formats or finite state machines.

 * My implementation deviates from the draft and the paper in some aspects.
   Sometimes, I found it difficult to follow the details in the description.
   Other times, the description was clear enough, but I made a conscious decision to deviate.
   A list of differences between the IETF draft and this implementation is given
   [below](#differences-between-the-ietf-draft-and-this-implementation).

## Network topology

The following figure shows a typical example network topology:

![Example network topology](figures/topology.png)

The topology consists of the following types of nodes:
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

Below, we describe the concepts of PSRD and key shares and each of these steps in more detail.

In the example scenario, clients Carol and Conny are responsible for producing an encryption key
and for delivering this key to encryptors Patrick and Porter respectively.
The other clients are faded out because they play no role in our example.

In our implementation, each client runs in a separate process, listening on a separate
HTTP port.

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

3. Relaying key shares from client to client.

Once again, we describe these steps in more detail below.

In the example scenario, all five hubs are involved in relaying the key shares between clients Carol
and Conny.

In our implementation, each hub also runs in a separate process, listening on a separate HTTP port.

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

In our implementation, the `manager.py` script takes on the role of the encryptors, invoking the
ETSI QKD 014 interface to request keys from the clients.

### Local distributors

The IETF draft has more more type of node: local distributors.
We have not implemented local distributors; hubs deliver PSRD directly to clients without
local distributors in between.

### Connectivity

The topology diagram above contains lines that represent the connectivity between the various
network nodes (clients, hubs, encryptors).
These lines are not intended to represent single-hop point-to-point physical connections.
Instead they represent potentially multi-hop IP connectivity between the network nodes; each link
may contain multiple switch or router hops.

## Interfaces

The topology contains the following software interfaces:
* DSKE interface (in-band and out-of-band).
* Key delivery interface.
* Management interface.

### DSKE interface

The DSKE interface is the interface between the clients and the hubs.
The clients and hubs run the DSKE protocol over this interface, which is described in detail
[below](#dske-protocol).
Using the DSKE protocol, the clients and the hubs collaborate with each other to establish the keys.

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
The point of this repository is not to have a full-blown implementation of ETSI QKD 014 but
rather to implement the DSKE protocol.
See [QuKayDee](https://qukaydee.com/) if you want to get experience with the ETSI QKD 014 protocol.

### Management interface

This repository contains a management script (`manager.py`) that is used to control the network
nodes.
It can start nodes, stop nodes, report the status of nodes, and request keys.
See the
[getting started guide](getting-started-guide.md)
or the
[user guide](user-guide.md)
for more information.
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
The key is split up into _n_ key shares, where _n_ is the number of hubs.
Each key share is relayed from the initiator client to the responder client through a different hub.

As a result of this arrangement:
1. An attacker needs to compromise at least _k_ hubs to recover the key.
2. The protocol is resilient against failures or denial-of-service attacks as long as at least
   _k_ hubs survive.

## Out-of-band versus in-band

Certain steps of the DSKE protocol, as described in the IETF draft, are not part of the DSKE
protocol per-se.
Instead, these steps are implemented using some secure mechanism that is outside of the scope of
the DSKE protocol itself.
We refer to these steps as out-of-band steps;
in ladder diagrams they are shown in red.
We refer to the steps that are actually part of the DSKE protocol itself as in-band steps;
in ladder diagrams they are shown in green.

The out-of-band steps include:
1. Clients registering themselves with hubs.
2. Hubs delivering Pre-Shared Random Data (PSRD) to clients.

The IETF draft gives some examples of how the out-of-band steps could be implemented in real life,
including physical delivery using Hardware Security Modules (HSMs), encrypted USBs, 
military
[key transfer devices](https://www.cryptomuseum.com/crypto/fill.htm)
, SIM cards, NFC, QKD, etc.

In our code we implement the out-of-band DSKE interface as an HTTP REST interface.
In real life, as we just mentioned, HTTP would not be used for this purpose; instead some secure
physical delivery mechanism would be used.
We use HTTP as a simulation of this physical mechanism to enable automated testing of use case
scenarios.

Our code also implements the in-band DSKE interface as an HTTP REST interface.
This REST interface runs over normal HTTP and not over HTTPS.
The DSKE protocol uses its own authentication and encryption mechanisms which are described
below.

## Pre-Shared Random Data (PSRD)

The concept of Pre-Shared Random Data (PSRD) plays a central role in the DSKE protocol.

Each client and each hub use some secure out-of-band mechanism to agree on large blocks of random
data, which we refer to as PSRD blocks.
The data is completely random and meaningless and should be generated by a high-quality entropy
source, for example a Quantum Random Number Generator (QRNG).
These blocks of PSRD can be very large, e.g. many gigabytes.

The random data in the PSRD blocks is consumed by the clients and by the hubs for the purpose
of authenticating DSKE protocol messages and for encrypting specific fields (namely the key shares)
in DSKE protocol messages.

Each byte of PSRD is used once and once only.
The PSRD is essentially used for One Time Pad (OTP) encryption, which contributes to the
Information Theoretic Security (ITS) of the protocol.

When the clients or the hubs run low on PSRD, there is an out-of-band mechanism for the clients
to request additional blocks of PSRD from the hubs.

In the code, each block of PSRD is represented by a `Block` object.
Each block is uniquely identified by a Universally Unique Identifier (UUID).

The clients and the hubs may have exchanged multiple PSRD blocks.
The pool of available PSRD blocks is represented by a `Pool` object.

When a client or a hub needs to authenticate or encrypt a DSKE message, it allocates
some bytes from the pool.
In the code, such an allocation is represented by an `Allocation` object.

An allocation may consist of multiple fragments from different blocks.
This happens when an allocation requests more bytes than are remaining in a block.
These fragments are represented in the code by `Fragment` objects.

One of the fundamental ideas in the DSKE protocol is that a given client and a given hub
can agree on a shared secret by exchanging the meta-data (and only the meta-data, not the data
itself) for an allocation.

As a simplified example, the client and the hub might agree to use an allocation that consists
of bytes 100 to 200 of PSRD block 11111111-2222-3333-4444-555555555555.
Given the range of bytes and the block UUID, both the client and the hub are able to retrieve the
shared secret data from their pool.
But any attacker cannot retrieve the shared secret data because the data itself is never on the wire
(only the meta-data) and the attacker does not have access to the PSRD.

For more details about the implementation see the [developer guide](developer-guide.md).

## Key relaying

The following two figures show how the DSKE protocol establishes a key between two clients Carol
and Conny.

Before they establish a key, client Carol and Conny have already obtained blocks of PSRD from
each hub using the DSKE out-of-band protocol (these are the red lines in the figures).

![Client to hub relaying](figures/client-to-hub-relaying.png)

The figure above shows the first half of the relaying process, namely relaying key shares
from a client Carol to all hubs.

 * Client Carol uses a Random Number Generator (RNG) to generate the key that she wishes to share
   with client Conny.

 * Client Carol uses Shamir's Secret Sharing (SSS) algorithm to split the key into _n_ key shares
   (or just shares for short), where _n_ is the number of hubs that is going to be used to relay
   the key.

 * Client Carol is going to send each share to a different hub, so that the hub can relay the share
   to the remote client Conny (second figure).

 * However, before client Carols sends a share to a particular hub, she first encrypts the share
   using an encryption key that is allocated from the PSRD pool associated with that particular
   hub.

 * When client Carol sends the encrypted key share to a hub, she include the meta-data about the
   encryption key to the hub.
   This allows the hub to retrieve the exact same decryption key from its local copy of the PSRD
   pool.

Note that the blue keys are different keys than the red keys in the figures.
The blue keys are the user keys that will be delivered to the encryptors.
These are split into key shares for relaying across the hubs.
The red keys are key share encryption keys.
These are allocated from the PSRD pools.

![Hub to client relaying](figures/hub-to-client-relaying.png)

The figure above shows the second half of the relaying process, namely relaying key shares
from all hubs to client Conny.

 * Client Conny receives and encrypted key share from each hob (to be more precise: from at least
   _k_ out of the _n_ hubs).

 * Along with the encrypted key share, the DSKE protocol message also contains meta-data about
   the encryption key that the hub used to encrypt the key share.

 * Client Conny uses this meta-data to allocate the description key from the PSRD pool associated
   with that particular hub and decrypt the encrypted message share.

 * Client Conny uses Shamir's Secret Sharing algorithm to reconstruct Carol's key from the
   decrypted key shares.

## Trusted Relay Nodes (TRNs)

In Quantum Key Distribution (QKD) there is the concept of Trusted Relay Nodes (TRNs).
Each QKD link has a maximum distance, and when you need to generate a QKD key across a greater
distance a trusted relay node can be used to relay the key.

The following figure shows how a trusted relay node works: the trusted relay node uses the red B-C
key to encrypt the green A-B node and relay it to node C.
After the relay is completed, the green A-B key becomes the end-to-end A-C key.

![Trusted Relay Node](figures/trusted-relay-node.png)

The problem with this approach is that the final A-C key (the green key) is not only known
by the end-points A and C but also by the relay node B.
You have to _trust_ that relay node B will not abuse or leak knowledge of the end-to-end key.
This is why B is called a _trusted_ relay node.

In Distribute Symmetric Key Encryption (DSKE) the problem of having to trust relay nodes is
addressed using Shamir Secret Sharing (SSS).
The secret key is split into _n_ key shares.
Each hub (which is a relay node) only knows one share of the key.
At least _k_ hubs would have to conspire with each other to be able to gain any knowledge of
the complete key.

This same mechanism also provides resilience to the DSKE protocol:
as long as there are _k_ surviving hub nodes, the DSKE protocol continues to work in the face
of hub failures (i.e. _n_ - _k_ hubs can fail).

## Message authentication


To protect against
[Man-in-the-middle attacks](https://en.wikipedia.org/wiki/Man-in-the-middle_attack)
all in-band DSKE protocol message must be
[authenticated](https://en.wikipedia.org/wiki/Authentication).

![Message Signing](figures/message-signing.png)

The above figure shows how messages sent from clients to hubs are authenticated
(messages sent from hubs to clients are authenticated in a similar way).

Client Carol signs sent messages as follows:

 * Client Carol wants to authenticate an in-band DSKE protocol message for hub Hank.
   This in-band DSKE message is an HTTP REST message that may contain query parameters and/or
   a message body.

 * Client Carol allocates a signing key from the PSRD pool associated with hub Hank.

 * Client Carol computes the signature for the message in the form of a
   [Hashed Message Authentication Code (HMAC)](https://en.wikipedia.org/wiki/HMAC)
   using the message to be signed and the allocated signing key as inputs.
   The HMAC signature is computed over the query parameters and the body of the signed message.

 * Client Carol attaches the computed singing key to the message using the HTTP
   header `DSKE-Signature`.
   This produces a signed message.

 * The `DSKE-Signature` header does not only contain the signature (i.e. the HMAC code)
   but also meta-data about the signature key.

Hub Hank validates the signature on received messages as follows:

 * Hub Hank extracts the following two piece of information from the `DSKE-Signature` header
   on the received message: (a) the meta-data for the signing key and (b) the HMAC signature.

 * Hub Hank retrieves the signing key from the PSRD pool associated with client Carol using
   the signing key meta-data extracted from the `DSKE-Signature` header.

 * Hub Hank performs its own local computation of the signature by computing the HMAC over
   the message received from Client Carol and the singing key retrieved from its local PSRD pool.

 * If the locally computed signature matches the received signature, the authentication succeeds.

Note that we don't authenticate out-of-band DSKE messages because the out-of-band REST messages are
only intended to simulated what would be a secure physical mechanism in real for automated testing
purposes.

## Pool ownership

So far, we have seen several scenarios where a node allocates a key from a local PSRD pool and
uses that key to encrypt a key share or to sign a DSKE message.
The node then sends meta-data about the allocated key to a peer node.
This allows the peer node to use the received key meta-data to retrieve the same key from its local
PSRD pool and decrypt the key share or to validate the signature.

Sometimes the node who allocates the key and sends the meta-data is a client and other times it
is a hub.
This leads to a race condition:
when two nodes (a client and hub) send a message to each other at roughly the same time,
it may happen that they allocate the same bytes from the PSRD pool.
When they receive the meta-data from their peer, they find that the bytes indicated in the received
meta-data are already allocated for a different purpose.

We solve this problem by having each node keep two separate PSRD pools: one pool from which the
client allocates bytes and a different pool from which the hub allocates bytes.
We refer to this as the concept of pool ownership: each PSRD pool is owned by either the client or
the hub.

## Client onboarding

Now that we have explained the basic concepts behind the DSKE protocol, we are finally ready to
describe the actual protocol in detail.
We start with client onboarding.

The following ladder diagram shows the onboarding of a new client in the network.
Note that all the steps in the ladder diagram are red, which means that they are all
[out-of-band](#out-of-band-versus-in-band)
steps.

![Client onboarding](figures/ladder-diagram-startup.png)

The steps for onboarding a new client into the network are as follows:

1. The client registers itself with each hub.

2. The client requests its initial block of Pre-Shared Random Data (PSRD) from each hub.

### Client registration

The first thing a client does after it starts up is to register itself with _each_ hub.
In the above example, both client Carol and client Conny register themselves with each of the five
hubs  Hank, Helen, Hilary, Holly, and Hugo.

The client knows which hubs to register itself with because the list of hub URLs is provided to the
client process as a command-line argument when it starts up.
In the current implementation, the hub is not provided with a lists of clients; it simply allows
can client to register itself.

If the hub is not yet running, the registration will fail.
In that case, the client periodically keeps retrying the registration.

The client registration is an HTTP PUT message.
As a result, the client registration is idem-potent and it is not an error for a client to register
itself multiple times. This can happen, for example, when a client crashes and restarts.

In the request, the client provides its own `client_name`.
In the response, the hub provides its `hub_name`.

Method: `PUT`

URL: `/hub/{hub_name}/dske/oob/v1/registration`

Request body:
```
{
  "client_name": "string"   # The name of the client.
}
```

Successful response body:
```
{
  "hub_name": "string"   # The name of the hub.
}
```

### Request Pre-Shared Random Data (PSRD)

Once a client has successfully registered itself with a particular hub, it requests its initial
blocks of Pre-Shared Random Data (PSRD) from that hub.
It requests one initial client-owned PSRD block and it requests one initial hub-owned PSRD block
(see discussion of PSRD block ownership above).

Each node consumes data from the PSRD blocks for key-share encryption and for message
authentication.
When a PSRD block nears the point of being fully consumed, the client will request a new PSRD block
to replenish the pool of PSRD data.

Method: `GET`

URL: `/hub/{hub_name}/dske/oob/v1/psrd`

Query parameters:

| Name | Type | Description |
|---|---|---|
| ```client_name``` | string | The client name. |
| ```owner``` | string | The owner of the PSRD block: `client` or `hub`. See discussion of PSRD block ownership above. |
| ```size``` | integer | The size in bytes of the requested PSRD block. |

Request body: None

Successful response body:
```
{
  "block_uuid": "string",   # A UUID chosen by the hub to uniquely identify the PSRD block.
  "data": "string"          # The random bytes in the PSRD block, as a base64 encoded string.
}
```
## Key establishment

The following ladder diagram shows the establishment of a new key:

![Key establishment](figures/ladder-diagram-get-key.png)

TODO: Complete this section

## Comparison with other key establishment protocols

DSKE provides the same functionality, namely key establishment (also referred to as key agreement
or key distribution) as some other protocols:

* Traditional classical protocols such as Diffie-Hellman (DH) and Elliptic Curve Diffie-Hellman
   (ECDH).

* Post-Quantum Cryptography (PQC) protocols such as the 
[Module-Lattice Key Encapsulation Mechanism (ML-KEM)](https://en.wikipedia.org/wiki/Kyber).

* Quantum Key Distribution (QKD) protocols such as 
[Bennett and Brassard 84 (BB84)](https://en.wikipedia.org/wiki/BB84).

The following table compares these protocols:

| Criterium | Traditional | PQC | QKD | DSKE |
|-|-|-|-|-|
| Needs special quantum hardware | No | No | Yes | No |
| Quantum safe | No | Yes | Yes | Yes |
| Based on hardness of mathematical problem | Yes (broken) | Yes (not broken) | No | No |
| Requires out-of-band distribution of information | No | No | No | Yes |


## Differences between the IETF draft and this implementation

In this section we describe the differences between the DSKE protocol as specified in
[draft-mwag-dske-02](https://datatracker.ietf.org/doc/draft-mwag-dske/02/)
and the DSKE protocol as implemented in this repository.

### Share generation and authentication scheme

The arXiv paper contains a very detailed detailed and mathematical description of exact algorithm
for generating the shares and for generating the authentication signature.
The draft contains a shorter description.
In both cases, we found the description complex and difficult to follow.
We are not sure that our implementation matches the paper and the draft exactly.
Once the project is more mature, we will attempt to contact the authors of the paper and draft to
validate our implementation's correctness.

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

### Local distributor

The IETF draft contains the concept of a local distributor, which sits between the hub and the
client.
Our code does not implement local distributors.

### Message wrapping

The draft calls for key establishment messages to be "_wrapped with Authenticated Encryption with
Associated Data (AEAD) mode ... whose primary purpose is anti-DoS, anonymity and confidentiality of
control data_".
We did not implement this since (according to the draft) this "_is not essential to the underlying
security of DSKE_."

### Initial keys

The draft calls the hub delivering a set of "_initial keys_" the the client when the client
registers itself with the hub.
The purpose of these initial keys is not clear from the draft;
we assume that they are used for message wrapping.
Since we did not implement message wrapping, we also did not implement the delivery of initial keys.

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
