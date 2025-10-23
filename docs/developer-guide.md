[Back to main page](/dske-python/)

# Developer guide

This page is intended for software developers;
it contains a high-level overview of the implementation.

For an overview of what Distributed Symmetric Key Establishment (DSKE) is and what problem it solves
see the [introduction](what-is-dske-and-what-problem-does-it-solve.md).

For a detailed description of the DSKE protocol, see the
[protocol guide](protocol-guide.md).

If you just want hands-on instructions on how to get started running the code and generating keys
with a minimum of background information see the
[getting started guide](getting-started-guide.md).
Or, for more details see the
[user guide](user-guide.md).

## Technology stack

The code technology stack includes:
* [Python 3.13](https://www.python.org/) as the programming language.
  The nodes (clients and hubs) are asynchronous;
  the manager is synchronous.
* [FastAPI](https://www.python.org/) for server-side HTTP APIs.
* [HTTPX](https://www.python-httpx.org/) for client-side HTTP APIs.
* [Uvicorn](https://uvicorn.dev/)as the ASGI (synchronous Server Gateway Interface) web server.
* [Git](https://git-scm.com/) and [Github](https://github.com/brunorijsman/dske-python) for version control.

The development toolchain includes:
* [Github actions](https://github.com/features/actions) for continuous integration.
* [Pylint](https://pypi.org/project/pylint/) for linting.
* [Black](https://black.readthedocs.io/) for code formatting.
* [Coverage](https://coverage.readthedocs.io/) for code coverage.
* [Pip](https://pypi.org/project/pip/) for dependency management.
* [Venv](https://docs.python.org/3/library/venv.html) for virtual environments.
* [Markdown](https://en.wikipedia.org/wiki/Markdown) for documentation.

## DSKE protocol

The Distributed Symmetric Key Establishment (DSKE) implementation in this repository is based on
IETF draft
[draft-mwag-dske-02](https://datatracker.ietf.org/doc/draft-mwag-dske/02/).
It has been developed completely independently of the authors of the draft, based only on the public
information in the draft.
See [the DSKE protocol page](dske-protocol.md) for more details.

## Proof of concept

The code is intended to be a proof-of-concept to study the DSKE protocol; it is not
suitable for  production deployments for numerous reasons (e.g. 
state is not persisted and the protocol needs to start from scratch every time a daemon restarts,
we have made no effort to prevent side-channel attacks,
etc.)

## Check-and-test script

The `check-and-test` bash script in the `scripts` directory does the following:
* Lints the code.
* Checks the formatting of the code.
* Runs all unit tests.
* Runs all system tests.
* Measures code coverage when running the tests.

A Github action workflow runs this script on every push to our repository.

The `--help` option explains it's usage:

<pre>
$ <b>scripts/check-and-test --help</b>
Usage: check-and-test [OPTIONS] [ACTION]

Positional arguments:
  ACTION:
    lint           Lint the code
    format-check   Check code formatting
    test           Run unit tests (including code coverage)

OPTIONS:
  -h, --help: Display this help message
  -v, --verbose: Verbose output
</pre>

When the script finishes it reports whether or not all checks and tests passed.
It also reports a code coverage report summary.
You can open a detailed code coverage report in your browser:

<pre>
$ <b>open htmlcov/index.html</b>
</pre>

## API endpoints

For full and up-to-date documentation of the API endpoints, each network node provides OpenAPI
documentation.
To view the documentation go to URL `http://localhost:PORT/docs` where PORT is the port number
for the network node as reported when the topology is started.

Here we provide a summary of the API endpoints and their purpose.

### API naming conventions

The API endpoints belong to one of the following groups:

| Endpoint path | Purpose |
|-|-|
| `.../dske/...` | DSKE protocol. |
 | `.../dske/oob/...` | The out-of-band (OOB) portion of the DSKE protocol. |
| `.../dske/api/...` | The in-band portion of the DSKE protocol. |
| `../mgmt/...` | Used for management. Since this code is not intended for production deployment, these endpoints are also not authenticated. |

All API endpoints include the node type and the node name at the start of the URL path.
For example:

| Node type | URL prefix |
|-|-|
| PUT | `/hub/HUB_NAME/...` |
| GET | `/client/CLIENT_NAME/...` |

Currently, this is not really necessary for anything, since each node runs in its own process
on a different HTTP port.
But we anticipate that we (or someone else) may run this code as a cloud-based service at some
point in the future (similar to what we did with
[QuKayDee](https://qukaydee.com) for QKD).
In that case, the cloud-based service would expose only a single HTTP port, and some proxy
(e.g [Nginx](https://nginx.org/)) would use URL-based routing to dispatch each request to the
correct node process.

All API endpoints are versioned (currently `v1`).

Putting all of this together, an example of a complete URL for one of the API endpoints is:
`/hub/HUB_NAME/dske/api/v1/key-share`

### Hub API endpoints

The hubs provides the following API endpoints:

| Method | URL | Purpose | Authenticated |
|-|-|-|-|
| PUT | `/hub/HUB_NAME /dske/oob/v1 /registration` | Register a client with a hub. | No |
| GET | `/hub/HUB_NAME /dske/oob/v1 /psrd` | A client gets a block of Pre-Shared Random Data (PSRD) from the hub. | No |
| POST | `/hub/HUB_NAME /dske/api/v1 /key-share` | An initiator client adds a key share to the hub. The share can later be retrieved by the responder client. | Yes |
| GET | `/hub/HUB_NAME /dske/api/v1 /key-share` | A responder client retrieves a key share from the hub. The share was previously added by the initiator client. | Yes |
| GET | `/hub/HUB_NAME /mgmt/v1 /status` | Get the management status of the hub. | No |
| POST | `/hub/HUB_NAME /mgmt/v1 /stop` | Stop the hub. | No |

### Clients API endpoints

The clients provides the following API endpoints:

| Method | URL | Purpose | Authenticated |
|-|-|-|-|
| GET | `/client/CLIENT_NAME /etsi/api/v1 /keys/SLAVE_SAE_ID/enc_keys` | An initiator encryptor gets a key from a client. | No |
| GET | `/client/CLIENT_NAME /etsi/api/v1 /keys/MASTER_SAE_ID/dec_keys ?key_ID=KEY_ID` | A responder encryptor gets a key with key ID from a client. | No |
| GET | `/client/CLIENT_NAME /etsi/api/v1 /keys/SLAVE_SAE_ID/status` | An encryptor gets the QKD link status from client. | No |
| GET | `/hub/HUB_NAME /mgmt/v1/status` | Get the management status of the client. | No |
| POST | `/hub/HUB_NAME /mgmt/v1/stop` | Stop the club. | No |

## Authentication

Only the in-band DSKE protocol API endpoints (`.../dske/api/...`) are authenticated
using the authentication mechanism described in the
[protocol guide](protocol-guide.md)

The out-of-band DSKE protocol API endpoints (`.../dske/oob/...`) are not authenticated.
They only exist to simulate actions that would be some secure out-of-band physical distribution
mechanism in real life for the purpose of automated testing.

The management API endpoints (`../mgmt/...`) are also not authenticated because this implementation
is not intended for production deployment.

And finally, the key delivery API endpoints (`.../etsi/api/...`) are also not authenticated because
we only implement a simplified subset of the
[ETSI QKD 014](https://www.etsi.org/deliver/etsi_gs/QKD/001_099/014/01.01.01_60/gs_qkd014v010101p.pdf)
key delivery interface.

TODO Continue from here

## Pre-Shared Random Data (PSRD) management

Pre-Shared Random Data (PSRD) is a central concept in DSKE.
This section summarizes how PSRD is implemented in the code.

### Class `Block`

The class `Block` represents a block PSRD bytes that the hub sends to the client.
The hub sends the block to the client using some secure out-of-band mechanism;
in our code this mechanism is represented by the `.../dske/oob/v1/psrd` REST interface endpoint.

The `Block` class has the following attributes:

| Attribute | Type | Purpose |
|-|-|-|
| block_uuid | UUID | Uniquely identifies the block. |
| size | int | Size of the block in bytes. |
| owned | bool | True is the block is owned: it is possible to both allocate and consume fragments from this block. False if the block is not owned: it is not possible to locally allocate fragments; it is only possible to consume fragments that have been allocated by the peer node. The concept of ownership is described in more detail below. |
| data | bytes | The bytes in the block. |
| allocated | bitarray | A bit for each byte in the block to indicate whether the byte is allocated. |
| consumed | bitarray | A bit for each byte in the block to indicate whether the byte is consumed. |

The state of each byte in the block is described by the following Finite State Machine (FSM):

![Block Finite State Machine (FSM)](figures/block-fsm.png)

When the block is created, each byte is unallocated.

The code can locally allocate bytes from the block.
A contiguous sequence of bytes allocated from a block is called a fragment.

Bytes that have been allocated can be consumed. The byte value used to encrypt or authenticate
a key share. The byte in the block is zeroed out.

It is also possible to consume bytes that have not been _locally_ allocated from a block.
This happens when the bytes have been _remotely_ allocated by the peer node, and the allocated
fragment is communicated through the DSKE protocol.

Under circumstances the code can return an allocated byte to the block without consuming it.
This is called deallocating the byte. Once a byte has been consumed, it can no longer be deallocated.

### Class `Fragment`

The class `Fragment` represents a contiguous sequence of bytes within a block that have been
allocated from that block.

The `Fragment` class has the following attributes:

| Attribute | Type | Purpose |
|-|-|-|
| block | Block | A reference to the block from which the fragment was allocated. |
| start_byte | int | The index of the byte within the block for the first byte in the fragment. |
| size | int | The number of bytes in the fragment. |
| value | bytes | A copy of the bytes in the block that have been allocated to the fragment. |
| consumed | bool | True if the bytes in the fragment has been consumed. False if the bytes in the fragment have only been allocated and not yet consumed. |

The relationship between a block and its fragments in shown in the following figure:

![Relation between block and fragments](figures/block-and-fragments.png)

### The concept of block ownership

When a hub and a client share a block of Pre-Shared Random Data (PSRD) there is a `Block` object
on the hub side and a `Block` object with the same random data on the client side.
The hub and the client use their blocks to allocate secrets that are shared with their peer.
These shared secrets are used for encryption and authentication of DSKE protocol messages.

In the code, allocating a shared secret means creating an `Allocation` object.
This marks some bytes in some blocks as being allocated and consumed.
Sharing a secret means sending the some information about the `Allocation` object to the peer:
which bytes in which blocks have been allocated, but not the byte values themselves.
The peer then uses this information to create a corresponding `Allocation` object with
identical byte values.
