# Developer guide

The code is implemented in Python 3.12 and uses FastAPI.

This repository contains an open source implementation of Distributed Symmetric Key Establishment (DSKE) as
specified in IETF draft
[draft-mwag-dske-02](https://datatracker.ietf.org/doc/draft-mwag-dske/02/).

## Proof of concept

The code is intended to be a proof-of-concept to study the DSKE protocol; it is not
suitable for  production deployments for numerous reasons (e.g. there are lots of side-channel 
vulnerabilities). 

It has been developed completely independently of the authors of the draft, based only on the public
information in the draft. 
It has been developed purely out of curiosity (building something is the best way to understand it).

## Implementation notes

The code is implemented in Python 3.12 and uses FastAPI.

TODO: Finish this