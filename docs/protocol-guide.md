# Protocol guide

This chapter describes the Distributed Symmetric Key Establishment (DSKE) protocol as it is
implemented in this repository.

My DSKE implementation is inspired by
[draft-mwag-dske](https://datatracker.ietf.org/doc/draft-mwag-dske/)
and by arXiv paper
[arXiv:2205.00615 Distributed Symmetric Key Establishment: A scalable, quantum-proof key distribution system](https://arxiv.org/abs/2205.00615).

I say "inspired by" because:

 * The draft and the paper only describe the general approach.
   They do not describe the protocol in sufficient detail for an unambiguous interoperable
   implementation.
   For example, the draft and the paper do not specify message formats or finite state machines.

 * My implementation deviates from the draft and the paper in some aspects.
   Sometimes, I found it difficult to follow the details in the description.
   Other times, the description was clear enough, but I made a conscious decision to deviate.
   See section TODO for a list of deviations.
