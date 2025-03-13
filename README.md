# Table of contents

* [Distributed Symmetric Key Establishment (DSKE)](#distributed-symmetric-key-establishment-dske)
* [The key distribution problem](#the-key-distribution-problem)
* [Authentication](#authentication)
* [The DSKE protocol described in draft-mwag-dske-01](#the-dske-protocol-described-in-draft-mwag-dske-01)
* [The open source implementation of DSKE in dske-python](#the-open-source-implementation-of-dske-in-dske-python)

# Distributed Symmetric Key Establishment (DSKE)

Distributed Symmetric Key Establishment (DSKE) is a method for parties to agree on a shared secret
(typically a symmetric encryption key) in a quantum-safe manner.

It is sometimes also referred to by other names, including Symmetric Key Agreement (SKA).

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
key establishment, shared secret establishment, symmetric key agreement, etc. etc. etc.

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
