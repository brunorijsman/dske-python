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
   See section TODO for a list of deviations.

## Encryptors, clients, and hubs

The network consists of three types of nodes: encryptors, clients, and hubs.


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
  Note: to avoid confusion we will use the term "key" to refer to the secret symmetric keys
  that are established between DSKE clients, and we will use the term "DSKE key" to refer
  to key material that is consumed from the pre-shared random data blocks to protect the DSKE
  protocol itself (i.e. to encrypt and authenticate DSKE protocol messages).
  
TODO: Add figures to clarify the above


This draft describes the protocol in general terms.
It does not (yet) describe the protocol in sufficient detail to enable interoperable
implementations.
For example, only the semantics but not yet the syntax of protocol messages is described.




