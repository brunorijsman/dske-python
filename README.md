# Table of contents

* [Distributed Symmetric Key Establishment (DSKE)](#distributed-symmetric-key-establishment-dske)
* [The key distribution problem](#the-key-distribution-problem)
* [Authentication](#authentication)
* [The DSKE protocol described in draft-mwag-dske-01](#the-dske-protocol-described-in-draft-mwag-dske-01)
* [The open source implementation of DSKE in dske-python](#the-open-source-implementation-of-dske-in-dske-python)

# Distributed Symmetric Key Establishment (DSKE)

Distributed Symmetric Key Establishment (DSKE) is a method for two (or more) parties to agree on a
symmetric encryption key. The method has the following special characteristics:

* It is Information Theoretically Secure (ITS). It method does not make any assumptions about
  computational constraints on the adversary.

* It is quantum-secure. This is a strengthening of the previous statement: even if the adversary
  has access to a quantum computer, the method remains secure.

* In particular, DSKE does not assume that the adversary cannot factor large numbers
  (which would break RSA), or that the adversary cannot compute large discrete logarithms
  (which would break DH and ECDH), or even that the adversary cannot solve Learning With Errors
  (LWE) problems (which would break ML-KEM).

* It allows any party to communicate with any party, without requiring that a Pre-Shared Key (PSK)
  must have been established out-of-band and a-priori for that specific pair of parties.

* It does require, however, that large blocks of Pre-Shared Random Data (PSRD) must have been
  shared out-of-band and a-priori between the communicating parties (known as DSKE clients) and 
  relay nodes (known as DSKE security hubs).

* These the DSKE security hubs are responsible for relaying the established keys between
  the communicating parties (i.e. between the DSKE clients).
  This relaying mechanism is both secure and resistant against Denial-of-Service (DoS) attacks.

* The symmetric key is broken up into _N_ parts, known as key shares, using an cryptographic
  algorithm called Shamir Secret Sharing (SSS).

* Each key share is distributed between the source DSKE client and the destination DSKE client
  using a different DSKE security hub.
  As a result, each DSKE security hub knows only a small part (namely a single key share) of
  the entire symmetric key.

* The destination DSKE client can reconstruct the symmetric keys by combining the key shares that
  it has received from multiple hubs.

* The destination DSKE client does not need the full set of _N_ key shares to reconstruct the
  key.
  The Shamir Secret Sharing (SSS) algorithm allows the key to be reconstructed using some smaller
  number of _K_ (where _K_ < _N_) key shares.

* Furthermore, the Shamir Secret Sharing (SSS) algorithm also guarantees that any party (such as
  and adversary) who has access to some key shares, but fewer than _K_ key shares, has zero
  knowledge about the key.
  In other words, it is not possible for the adversary to reconstruct some partial knowledge of
  the key by having some subset of the required _K_ key shares.

* This means that the adversary would have to simultaneously successfully compromise at least _K_
  DSKE security hubs to be able to recover the key from the observed key shares.
  In other words, while the DSKE security hubs do have some aspects of being a Trusted Relay Node
  (TRN), compromising a single relay node is not enough get the key;
  the adversary has to compromise at least _K_ relay nodes at the same time.

* The protocol is also resilient against Denial of Service (DOS) attacks and failures.
  The key shares are relayed over _N_ distinct paths (i.e. through _N_ different DSKE security
  hubs).
  If some number of the paths fail because of a fiber cut or a node failure, the end-to-end
  key establishment protocol still succeeds, as long as _K_ paths remain functional (i.e.
  as long as no more than _N-K_ paths fail).

* All communications between DSKE clients and DSKE hubs are both One-Time Pad (OTP) encrypted and
  authenticated using single-use keys extracted from the pre-shared random data.
  Note: to avoid confusion we will use the term "user key" to refer to the secret symmetric keys
  that are established between DSKE clients, and we will use the term "DSKE key" to refer
  to key material that is consumed from the pre-shared random data blocks to protect the DSKE
  protocol itself (i.e. to encrypt and authenticate DSKE protocol messages).
  
DSKE is described in detail in the following arXiv papers:

 * arXiv:2205.00615:<br>
   Distributed Symmetric Key Establishment: A scalable, quantum-proof key distribution system.<br>
   [https://arxiv.org/abs/2205.00615](https://arxiv.org/abs/2205.00615)

 * arXiv:2304.13789<br>
   Composable Security of Distributed Symmetric Key Establishment Protocol.<br>
   [https://arxiv.org/abs/2304.13789]](https://arxiv.org/abs/2304.13789)

There is also an Internet Engineering Task Force (IETF) Internet-Draft (I-D):

* draft-mwag-dske-01<br>
  The Distributed Symmetric Key Establishment (DSKE) Protocol.<br>
  [https://datatracker.ietf.org/doc/draft-mwag-dske/01/](https://datatracker.ietf.org/doc/draft-mwag-dske/01/)

This draft describes the protocol in general terms.
It does not (yet) describe the protocol in sufficient detail to enable interoperable
implementations.
For example, only the semantics but not yet the syntax of protocol messages is described.

# The key distribution problem

The problem that DSKE solves is the problem of Symmetric Key Establishment (SKE).

When two parties wish to securely communicate by exchanging encrypted data, they typically use
a symmetric encryption protocol such as the
[Advanced Encryption Standard (AES)](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.197-upd1.pdf)
.

All symmetric encryption protocols require the two communicating parties to first agree on an
encryption key.
This encryption key must be secret: it must only be known to the two parties and not to any
unauthorized eavesdropper who is attempting to steal the data.

The question of how the two parties get this secret symmetric key is known as the Symmetric
Key Establishment (SKE) problem.
Symmetric key exchange is also known by many other names, including key distribution, key agreement,
key establishment, shared secret establishment, Symmetric Key Agreement (SKA), etc.

There are several existing mechanisms and protocols for doing key distribution:

1. **Pre-Shared Keys (PSK)**
   
   The symmetric keys are distributed using some Out-of-Band (OOB) mechanism and pre-configured
   on the communicating encryptor devices.
   An example of such an out-of-band mechanism is that a trusted person, who can identify him or
   herself, hand-carries a tamper-proof storage devices that contains the symmetric keys.

   Pre-shared keys have several disadvantages.

   It is cumbersome and error-prone because it requires some secure out-of-band mechanism to
   distribute the keys.
   In practice, because it is so cumbersome, pre-shared keys are not rolled-over as often as they
   should.

   It is not possible to securely communicate with a party unless a pre-shared key has been
   established with that specific party a-priori. For example, securely communicating with websites
   is impractical using pre-shared keys.

2. **Traditional classical cryptographic algorithms for dynamic key establishment**

   The vast majority of secure communications on the Internet today use what we refer to 
   (for lack of a better name) as "traditional classical cryptographic algorithms for
   dynamic key establishment". 
   This includes cryptographic algorithms such as Diffie-Hellman (DH), 
   Elliptic Curve Diffie-Hellman (ECDH), and Rivest Shamir Adleman (RSA).

   All of these protocol enable two communicating parties who have never met before to dynamically
   generate a symmetric encryption key (referred to as a session key) for the duration of the
   communication session.
   Generating the key involves the two parties exchanging some messages using a so-called
   key generation protocol.
   One example of such a key generation protocol is the Internet Key Exchange (IKE) protocol.

   The interesting thing is that the key generation protocol is allowed to be a public discourse
   and still be safe.
   What this means that is impossible for an attacker (typically called an eavesdropper) to
   figure out what the dynamically generated key is, _even_ if the attacker can view all messages
   that are part of the key generation protocol.

   All of the cryptographic algorithms that we mentioned (DH, ECDH, RSA) rely on mathematical
   trap-door functions.
   These are functions that are easy to compute in one direction, but practically impossible to
   compute in the reverse direction.
   For example, it is easy to multiple two large numbers and determine their product.
   But it is practically impossible to find the original two numbers given the product, i.e.,
   to factor a number into primes.
   The security of RSA depends on this property.
   The security of DH and ECDH relies on a similar trapdoor function involving computing the
   exponents of certain special numbers (a to the power b).

3. **Post Quantum Cryptography (PQC)**

   TODO: Finish this

4. **Quantum Key Distribution (QDK)**

   TODO: Finish this
   
# Authentication

The problem of key distribution is very closely related to the problem of authentication.

TODO: Finish this

# The DSKE protocol described in draft-mwag-dske-01

TODO: Finish this

# The open source implementation of DSKE in dske-python

This repository contains an implementation of Distributed Symmetric Key Establishment (DSKE) as specified in IETF draft
[draft-mwag-dske-01](https://datatracker.ietf.org/doc/draft-mwag-dske/01/).
The code is implemented in Python 3.12 and uses FastAPI.

**WARNING**: This project is in the extremely early stages of implementation and nowhere near usable yet.

To start the DSKE topology:

<pre>
$ <b>./manager.py topology.yaml start</b>
Starting hub helen on port 8000
Starting hub hank on port 8001
Starting hub heidi on port 8002
Starting hub harry on port 8003
Starting hub holly on port 8004
Starting client clarice on port 8005
Starting client charlie on port 8006
Starting client camila on port 8007
Starting client colin on port 8008
Starting client cindy on port 8009
</pre>

Once a topology has been started, open the API in the browser at URL `http://127.0.0.1:8000/docs`.
(Replace 8000 with the port number reported by the topology start command)

To stop the DSKE topology:

<pre>
$ <b>./manager.py topology.yaml stop</b>
Stopping client clarice on port 8005
Stopping client charlie on port 8006
Stopping client camila on port 8007
Stopping client colin on port 8008
Stopping client cindy on port 8009
Stopping hub helen on port 8000
Stopping hub hank on port 8001
Stopping hub heidi on port 8002
Stopping hub harry on port 8003
Stopping hub holly on port 8004
</pre>
