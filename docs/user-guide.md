[Back to main page](/dske-python/)

# User guide

This page contains detailed end-user documentation.
It describes how to use the `manager.py` script to start and stop topologies and to generate
keys.

For an overview of what Distributed Symmetric Key Establishment (DSKE) is and what problem it solves
see the [introduction](what-is-dske-and-what-problem-does-it-solve.md).

If you just want hands-on instructions on how to get started running the code and generating keys
with a minimum of background information see the
[getting started guide](getting-started-guide.md).

For a detailed description of the DSKE protocol, see the
[protocol guide](protocol-guide.md).

If you are a software developer and would like more details about the implementation, see the
[developer guide](developer-guide.md).

## Configuration file

We first need a configuration YAML file which describes the topology of the network.
It lists the names of 
the DSKE security hubs (hubs for short),
the DSKE clients (clients for short),
and the encryptors.
.

The repository contains an example `dske-config.yaml` file, which is the default configuration.
In this example output, we have removed all the comments, showing only the active parts of the
configuration:

<pre>
$ <b>cat dske-config.yaml</b>
hubs:
  - name: hank
  - name: helen
  - name: hilary
  - name: holly
  - name: hugo
clients:
  - name: carol
    encryptors:
      - name: sam
  - name: celia
    encryptors:
      - name: serena
  - name: cindy
  - name: connie
    encryptors:
      - name: sofia
  - name: curtis
    encryptors:
      - name: sunny
      - name: susan
</pre>

## The topology manager

The script `manager.py` is used to:
* Start a topology.
* Stop a topology.
* Retrieve the status of one or more nodes.
* Retrieve keys from client nodes.

Use the `--help` option to see the command line parameters:

<pre>
$ <b>./manager.py --help</b>
usage: manager.py [-h] [--config CONFIG_FILE] [--client CLIENT] [--hub HUB] {start,stop,status,etsi-qkd} ...

DSKE Manager

positional arguments:
  {start,stop,status,etsi-qkd}
    start               Start all hubs and clients
    stop                Stop all hubs and clients
    status              Report status for all hubs and clients
    etsi-qkd            ETSI QKD operations

options:
  -h, --help            show this help message and exit
  --config CONFIG_FILE  Configuration file name (default: dske-config.yaml)
  --client CLIENT       Filter on client name
  --hub HUB             Filter on hub name
</pre>

## Start the topology

To start all nodes in the DSKE topology, use the manager `start` command:

<pre>
$ <b>./manager.py start</b>
Waiting for all nodes to be stopped
Starting hub hank on port 8100
Starting hub helen on port 8101
Starting hub hilary on port 8102
Starting hub holly on port 8103
Starting hub hugo on port 8104
Starting client carol on port 8105
Starting client celia on port 8106
Starting client cindy on port 8107
Starting client connie on port 8108
Starting client curtis on port 8109
Waiting for all nodes to be started
</pre>

The output reports that 10 nodes are started in total: 5 hub nodes (hank, helen, hilary, holly,
and hugo) and 5 client nodes (carol, celia, cindy, connie, and curtis).

The reported port numbers (8100, 8101, etc.) are the TCP port numbers for the REST interface of
each node.

## Stop the topology

To stop all nodes in the topology, use the manager `stop` command:

<pre>
$ <b>./manager.py stop</b>
Stopping client curtis on port 8109
Stopping client connie on port 8108
Stopping client cindy on port 8107
Stopping client celia on port 8106
Stopping client carol on port 8105
Stopping hub hugo on port 8104
Stopping hub holly on port 8103
Stopping hub hilary on port 8102
Stopping hub helen on port 8101
Stopping hub hank on port 8100
Waiting for all nodes to be stopped
</pre>

## One background process per node

Starting a topology spawns one Python background process for each node. 
You can see these processes using `ps` command:

<pre>
 $ <b>ps | grep Python</b>
42176 ttys000    0:01.28 Python -m hub hank --port 8100
42177 ttys000    0:01.27 Python -m hub helen --port 8101
42178 ttys000    0:01.27 Python -m hub hilary --port 8102
42179 ttys000    0:01.26 Python -m hub holly --port 8103
42180 ttys000    0:01.26 Python -m hub hugo --port 8104
42181 ttys000    0:01.67 Python -m client carol --port 8105 --encryptors sam --hubs http://127.0.0.1:8100/hub/hank http://127.0.0.1:8101/hub/helen http://127.0.0.1:8102/hub/hilary http://127.0.0.1:8103/hub/holly http://127.0.0.1:8104/hub/hugo
42182 ttys000    0:01.65 Python -m client celia --port 8106 --encryptors serena --hubs http://127.0.0.1:8100/hub/hank http://127.0.0.1:8101/hub/helen http://127.0.0.1:8102/hub/hilary http://127.0.0.1:8103/hub/holly http://127.0.0.1:8104/hub/hugo
42183 ttys000    0:01.65 Python -m client cindy --port 8107 --hubs http://127.0.0.1:8100/hub/hank http://127.0.0.1:8101/hub/helen http://127.0.0.1:8102/hub/hilary http://127.0.0.1:8103/hub/holly http://127.0.0.1:8104/hub/hugo
42184 ttys000    0:01.65 Python -m client connie --port 8108 --encryptors sofia --hubs http://127.0.0.1:8100/hub/hank http://127.0.0.1:8101/hub/helen http://127.0.0.1:8102/hub/hilary http://127.0.0.1:8103/hub/holly http://127.0.0.1:8104/hub/hugo
42185 ttys000    0:01.64 Python -m client curtis --port 8109 --encryptors sunny susan --hubs http://127.0.0.1:8100/hub/hank http://127.0.0.1:8101/hub/helen http://127.0.0.1:8102/hub/hilary http://127.0.0.1:8103/hub/holly http://127.0.0.1:8104/hub/hugo
...
</pre>

## Waiting for nodes to be started

It takes some time for each background process to startup and to get to the point that the
process is ready to accept and process incoming requests over its REST interfaces.
If we try to invoke any REST API before the node is fully started, we will get an error.
This is why the `start` command explicitly waits for all nodes to be started (it
reports `Waiting for all nodes to be started` at the end):

<pre>
$ <b>./manager.py start</b>
Waiting for all nodes to be stopped
Starting hub hank on port 8100
...
Starting client curtis on port 8109
<b>Waiting for all nodes to be started</b>
</pre>

## Waiting for nodes to be stopped

Similarly, it takes some time for each background process to completely stop and get to the
point that the TCP port number can be used again for restarting a node on the same TCP port again.
Even if the background process is completely stopped, the TCP port number can get stuck in
state TIME_WAIT and it can take the operating system up to 60 seconds to release the TCP port.
This is why the `start` command explicitly waits for all needed TCP ports to be available
(it reports `Waiting for all nodes to be stopped` at the beginning).

<pre>
$ <b>./manager.py start</b>
<b>Waiting for all nodes to be stopped</b>
Starting hub hank on port 8100
...
Starting client curtis on port 8109
Waiting for all nodes to be started
</pre>

If it takes longer than expected for a node to stop and for the TCP port to become available again
(i.e. to exist from state TIME_WAIT) the stop command will periodically report that it is still
waiting (this should not take longer than 60 seconds):

<pre>
$ <b>./manager.py stop</b>
Stopping client curtis on port 8109
...
Stopping hub hank on port 8100
Waiting for all nodes to be stopped
<b>Still waiting for client connie to be stopped
Still waiting for client connie to be stopped
Still waiting for client connie to be stopped</b>
</pre>

## The `--client` and `--hub` command line options

The manager command line option `--client CLIENT` can be used to apply a command to a single
client node.
For example, to start one individual client carol:

<pre>
$ <b>./manager.py --client carol start</b>
Waiting for client carol to be stopped
Starting client carol on port 8105
Waiting for client carol to be started
</pre>

Similarly, the manager command line option `--hub HUB` can be used to apply a command to a single
hub node.
For example, to stop one individual hub hugo:

<pre>
$ <b>./manager.py --hub hugo stop</b>
Stopping hub hugo on port 8104
Waiting for hub hugo to be stopped
</pre>

You can use the `--client` and `--hub` command line options multiple times.
For example:

<pre>$ <b>./manager.py --client carol --client corrie --hub hank start</b>
Waiting for client carol, client corrie, hub hank to be stopped
Starting hub hank on port 8100
Starting client carol on port 8105
Waiting for client carol, client corrie, hub hank to be started
</pre>

## Starting and stopping nodes directly

Behind the scenes, the `manager.py` script spawns a separate Python process each client node
and for each hub node.
If you so desire, you can also start these Python processes manually.

The Python module `client` implements the client node process.
Use the `--help` option to see its usage:

<pre>
$ <b>python -m client --help</b>
usage: client [-h] [--port PORT] [--start-request-psrd_threshold START_REQUEST_PSRD_THRESHOLD] [--stop-request-psrd-threshold STOP_REQUEST_PSRD_THRESHOLD]
              [--get-psrd-block-size GET_PSRD_BLOCK_SIZE] [--min-nr-shares MIN_NR_SHARES] [--hubs HUBS [HUBS ...]] [--encryptors ENCRYPTORS [ENCRYPTORS ...]]
              name

DSKE Client

positional arguments:
  name                  Client name

options:
  -h, --help            show this help message and exit
  --port PORT           Port number
  --start-request-psrd_threshold START_REQUEST_PSRD_THRESHOLD
                        Start request PSRD threshold (default: 500)
  --stop-request-psrd-threshold STOP_REQUEST_PSRD_THRESHOLD
                        Stop request PSRD threshold (default: 2000)
  --get-psrd-block-size GET_PSRD_BLOCK_SIZE
                        Request PSRD block size (default: 2000)
  --min-nr-shares MIN_NR_SHARES
                        Minimum number of shares (default: 3)
  --hubs HUBS [HUBS ...]
                        Base URLs for hubs (e.g., http://127.0.0.1:8100)
  --encryptors ENCRYPTORS [ENCRYPTORS ...]
                        Names (SAE IDs) of encryptors consuming keys from this client (KME).
</pre>

The typical usage is to provide the client name, the port number, a list of base URLs for
the hubs in the network, and a list of encryptors attached to the client: For example:

<pre>
$ <b>python -m client carol --port 8105 --hubs http://127.0.0.1:8100/hub/hank http://127.0.0.1:8101/hub/helen http://127.0.0.1:8102/hub/hilary http://127.0.0.1:8103/hub/holly http://127.0.0.1:8104/hub/hugo --encryptors sam</b>
</pre>

Similarly, the Python module `hub` implements the client node process.
Use the `--help` option to see its usage:

<pre>
$ <b>python -m hub --help</b>
usage: hub [-h] [-p PORT] name

DSKE Hub

positional arguments:
  name             Hub name

options:
  -h, --help       show this help message and exit
  -p, --port PORT  Port number
</pre>

The typical usage is to provide the hub name and the port number.

<pre>
$ <b>python -m hub helen --port 8101</b>
</pre>

As you can see, manually starting clients and hubs involves typing long error-prone commands
and requires some book-keeping about which node uses which TCP port number.
This is why the `manager.py` script exists;
it collects all the necessary information from the topology file and starts all the nodes with
the correct (long) command-line arguments.

## ETSI QKD 014 Get key

Use the manager `get-key` sub-command under the `etsi-qkd` command to invoke the ETSI QKD 014
"Get Key" API to retrieve a key for a pair of SAEs on the master SAE.

The `get-key` sub-command has the following command-line options:

<pre>
$ <b>./manager.py etsi-qkd sam sunny get-key --help</b>
usage: manager.py configfile etsi-qkd master_sae_id slave_sae_id get-key [-h] [--size SIZE]

options:
  -h, --help   show this help message and exit
  --size SIZE  Key size in bits
</pre>

In the following example we invoke the Get Key API for the QKD link between master SAE Sam and
slave SAE Serena:

<pre>
 $ <b>./manager.py etsi-qkd sam serena get-key</b>
Invoke ETSI QKD Get Key API on client (KME) carol port 8105 master encryptor (SAE) sam slave encryptor (SAE) serena:
{
  "keys": {
    "key_ID": "f1f2cf55-9569-4e8f-8805-f80c8f600d48",
    "key": "+bXUKbPwVSdpS23JXGLSRA=="
  }
}
</pre>

The master / slave terminology comes from ETSI QKD 014 version 1 and will be revised in version 2.

## ETSI QKD 014 Get key with key IDs

Use the manager `get-key-with-key-ids` sub-command under the `etsi-qkd` command to invoke the 
ETSI QKD 014 "Get Key" API to retrieve a key for a pair of SAEs on the slave SAE.

The `get-key` sub-command has the following command-line options:

<pre>
$ <b>./manager.py etsi-qkd sam serena get-key-with-key-ids --help</b>
usage: manager.py configfile etsi-qkd master_sae_id slave_sae_id get-key-with-key-ids [-h] key_id

positional arguments:
  key_id      Key ID

options:
  -h, --help  show this help message and exit
</pre>

In the following example we invoke the Get Key with Key IDs API for the QKD link between master 
SAE Sam and slave SAE Serena, where the Key ID is d6a116f1-104e-4213-8cf1-0557cf33cb29 (this is the
Key ID returned by the Get Key API call above):

<pre>
$ <b>./manager.py etsi-qkd sam serena get-key-with-key-ids 6a116f1-104e-4213-8cf1-0557cf33cb29</b>
Invoke ETSI QKD Get Key with Key IDs API on client (KME) celia port 8106 master encryptor (SAE) sam slave encryptor (SAE) serena:
{
  "keys": [
    {
      "key_ID": "f1f2cf55-9569-4e8f-8805-f80c8f600d48",
      "key": "+bXUKbPwVSdpS23JXGLSRA=="
    }
  ]
}
</pre>

## ETSI QKD 014 Get key pair

As a matter of convenience, there is also a `get-key-pair` sub-command to combine both the
"Get key" and the "Get key with key IDs" calls.

The `get-key-pair` sub-command has the following command-line options:

<pre>
$ <b>./manager.py etsi-qkd carol curtis get-key-pair --help</b>
usage: manager.py configfile etsi-qkd master_sae_id slave_sae_id get-key-pair [-h] [--size SIZE]

options:
  -h, --help   show this help message and exit
  --size SIZE  Key size in bits
</pre>

In the following example, we ask for a key pair between master SAE Sam and slave SAE Sunny:

<pre>
$ <b>./manager.py etsi-qkd sam sunny get-key-pair</b>
Invoke ETSI QKD Get Key API on client (KME) carol port 8105 master encryptor (SAE) sam slave encryptor (SAE) sunny:
{
  "keys": {
    "key_ID": "4b700076-9691-4935-9e9b-707c1425fd29",
    "key": "JmaqM91DsWC/qlawABoVOw=="
  }
}
Invoke ETSI QKD Get Key with Key IDs API on client (KME) curtis port 8109 master encryptor (SAE) sam slave encryptor (SAE) sunny:
{
  "keys": [
    {
      "key_ID": "4b700076-9691-4935-9e9b-707c1425fd29",
      "key": "JmaqM91DsWC/qlawABoVOw=="
    }
  ]
}
Key values match
</pre>

And, finally, there is a `status` subcommand to invoke the "Status" ETSI QKD 014 API:

<pre>
$ <b>./manager.py etsi-qkd sam sunny get-status</b>
Invoke ETSI QKD Status API on client (KME) carol port 8105 master encryptor (SAE) sam slave encryptor (SAE) sunny:
{
  "source_kme_id": "carol",
  "target_kme_id": "",
  "master_sae_id": "sam",
  "slave_sae_id": "sunny",
  "key_size": 128,
  "stored_key_count": 100,
  "max_key_count": 1000,
  "max_key_per_request": 1,
  "max_key_size": 16777216,
  "min_key_size": 32,
  "max_sae_id_count": 0
}
</pre>

## Report the topology status

Use the manager `status` command (not to be confused with the `etsi-qkd status` command)
to report the status of each node in the topology:

<pre>
$ <b>./manager.py status</b>
Status for hub hank on port 8100
{
  "name": "hank",
  "peer_clients": [
    {
      "client_name": "carol",
      "local_pool": {
        "blocks": [
          {
            "uuid": "4cb97ab1-0e3f-4f48-a0d7-90de58e85d53",
            "size": 2000,
            "data": "AAAAAAAAAAAAAA==...",
            "nr_used_bytes": 32,
            "nr_unused_bytes": 1968
          }
        ],
        "owner": "local"
      },
      "peer_pool": {
        "blocks": [
          {
            "uuid": "c142de3a-8464-440f-bbfd-78937481732a",
            "size": 2000,
            "data": "AAAAAAAAAAAAAA==...",
            "nr_used_bytes": 48,
            "nr_unused_bytes": 1952
          }
        ],
        "owner": "peer"
      }
    },
    ... snip ...
  ]
}
</pre>

You can also use the `--client` or `--hub` command-line option to only report the status of a single
client or hub node, for example:

<pre>
$ <b>./manager.py --client celia status</b>
Status for hub hank on port 8100
{
  "name": "hank",
  "peer_clients": [
    {
      "client_name": "carol",
      "encryptor_names": [
        "sam"
      ],
      "local_pool": {
        "blocks": [
          {
            "uuid": "192c0144-ffec-4f95-9a9f-7d7a82310be7",
            "size": 2000,
            "data": "AAAAAAAAAAAAAA==...",
            "nr_used_bytes": 192,
            "nr_unused_bytes": 1808
          }
        ],
        "owner": "local"
      },
      "peer_pool": {
        "blocks": [
          {
            "uuid": "46627eb9-7e0d-4d40-8d67-8747f32a92f5",
            "size": 2000,
            "data": "AAAAAAAAAAAAAA==...",
            "nr_used_bytes": 288,
            "nr_unused_bytes": 1712
          }
        ],
        "owner": "peer"
      }
    },
    ... snip ...
  ]
}
</pre>

A useful trick is to use the `tail -n +2` command to skip the first line of output, and to pipe
the remaining output (which is JSON) through the `jq` command to colorize the JSON output:

<pre>
$ <b>./manager.py --client carol status | tail -n +2 | jq</b>
{
  "name": "carol",
  "encryptor_names": [
    "sam"
  ],
  "peer_hubs": [
    {
      "hub_name": "hank",
      "registered": true,
      "local_pool": {
        "blocks": [
          {
            "uuid": "46627eb9-7e0d-4d40-8d67-8747f32a92f5",
            "size": 2000,
            "data": "AAAAAAAAAAAAAA==...",
            "nr_used_bytes": 288,
            "nr_unused_bytes": 1712
          }
        ],
        "owner": "local"
      },
      "peer_pool": {
        "blocks": [
          {
            "uuid": "192c0144-ffec-4f95-9a9f-7d7a82310be7",
            "size": 2000,
            "data": "AAAAAAAAAAAAAA==...",
            "nr_used_bytes": 192,
            "nr_unused_bytes": 1808
          }
        ],
        "owner": "peer"
      }
    },
    ... snip ...
  ]
}
</pre>

Even better, you can use the `pq` command with a query to look for specific fields in the JSON
output.
In the following example we display the information about the local pool for peer-hub hank
on client carol:

<pre>
$ <b>./manager.py --client carol status | tail -n +2 | jq '(.peer_hubs[] | select(.hub_name == "hank") .local_pool)'</b>
{
  "blocks": [
    {
      "uuid": "46627eb9-7e0d-4d40-8d67-8747f32a92f5",
      "size": 2000,
      "data": "AAAAAAAAAAAAAA==...",
      "nr_used_bytes": 288,
      "nr_unused_bytes": 1712
    }
  ],
  "owner": "local"
}
</pre>

## Log files

Each node produces an `.out` log file for debugging purposes.
The information in this log file will vary wildly as the implementation progresses.
For example, the log file for client carol is `client-carol.out`:

<pre>
$ <b>cat client-carol.out</b>
INFO:     Started server process [24907]
INFO:     Waiting for application startup.
INFO:     Begin register task for peer hub None
INFO:     Begin register task for peer hub None
INFO:     Begin register task for peer hub None
INFO:     Begin register task for peer hub None
INFO:     Begin register task for peer hub None
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8105 (Press CTRL+C to quit)
INFO:     Call PUT http://127.0.0.1:8100/hub/hank/dske/oob/v1/registration 200
INFO:     Finish register task for peer hub None
INFO:     Call PUT http://127.0.0.1:8103/hub/holly/dske/oob/v1/registration 200
INFO:     Call PUT http://127.0.0.1:8102/hub/hilary/dske/oob/v1/registration 200
INFO:     Call PUT http://127.0.0.1:8104/hub/hugo/dske/oob/v1/registration 200
INFO:     Call PUT http://127.0.0.1:8101/hub/helen/dske/oob/v1/registration 200
INFO:     Begin request PSRD task for peer hub hank and pool owner local
INFO:     Begin request PSRD task for peer hub hank and pool owner peer
INFO:     Finish register task for peer hub None
INFO:     Finish register task for peer hub None
INFO:     Finish register task for peer hub None
INFO:     Finish register task for peer hub None
INFO:     Begin request PSRD task for peer hub holly and pool owner local
INFO:     Begin request PSRD task for peer hub holly and pool owner peer
INFO:     Begin request PSRD task for peer hub hilary and pool owner local
INFO:     Begin request PSRD task for peer hub hilary and pool owner peer
INFO:     Begin request PSRD task for peer hub hugo and pool owner local
INFO:     Begin request PSRD task for peer hub hugo and pool owner peer
INFO:     Begin request PSRD task for peer hub helen and pool owner local
INFO:     Begin request PSRD task for peer hub helen and pool owner peer
INFO:     Call GET http://127.0.0.1:8100/hub/hank/dske/oob/v1/psrd?client_name=carol&pool_owner=client&size=2000 200
INFO:     Finish request PSRD task for peer hub hank and pool owner local
INFO:     Call GET http://127.0.0.1:8100/hub/hank/dske/oob/v1/psrd?client_name=carol&pool_owner=hub&size=2000 200
INFO:     Finish request PSRD task for peer hub hank and pool owner peer
INFO:     Call GET http://127.0.0.1:8104/hub/hugo/dske/oob/v1/psrd?client_name=carol&pool_owner=client&size=2000 200
INFO:     Finish request PSRD task for peer hub hugo and pool owner local
... snip ...
</pre>

## REST interfaces

The nodes communicate with each other over REST interfaces, implemented using FastAPI.
There are four types of REST interfaces:

1. `api` REST interfaces model the actual DSKE protocol specified in the draft. 
   Note that the draft currently only describes the protocol at the semantic level, and not (yet)
   the message encoding. 
   We do not intend to imply that REST is the best encoding for the message encoding; a leaner 
   binary encoding may be more appropriate for this type of protocol.
   We only chose REST to make prototyping and studying the protocol easier the semantic level.

2. `oob` REST interfaces model the out-of-band actions mentioned in the draft, for example 
   delivering a block of pre-shared random data (PSRD).
   In real life, this would not be done over a REST interface but using some other mechanism
   (e.g. physically shipping a tamper-proof device with gigabytes of random data). 
   In this code we use REST interface to model these actions so that we can automate the scripting
   of entire end-to-end testing scenarios.

3. `esti` REST interfaces are implement the ETSI QKD 014 interface (a subset at this time) on the
   DSKE clients to deliver the produced keys to the Secure Application Entity (SAE) consumers.

4. `mgmt` management REST interfaces to control and debug the various nodes (e.g. to stop them and
   to retrieve operational status to "look inside" of them to see what is happening).

## REST interface documentation

The REST interface for each node is available at the reported port number when the topology was
started.

In the above example, the REST interface for hub "Hank" is available at `http://127.0.0.1:8100`

In addition to the REST interface itself, documentation is also available at
`http://127.0.0.1:8100/docs` and `http://127.0.0.1:8100/redoc`.
You can also manually invoke the REST APIs from the documentation page (click on an API endpoint
and then click on "Try it out").

Here is an example of the automatically generated documentation at `http://127.0.0.1:8105/docs`
for a client node:

![Client REST API documentation](figures/client-rest-api-documentation.png)

Here is an example of the automatically generated documentation at `http://127.0.0.1:8100/docs`
for a hub node:

![Hub REST API documentation](figures/hub-rest-api-documentation.png)

When you click on the row for `POST /dske/hub/api/v1/key-share` you see the detailed documentation
for that particular REST endpoint:

![Hub POST key-share details documentation](figures/hub-post-key-share-endpoint-details-documentation.png)

### Invoking the REST interface

Here is an example of invoking the API to get the status of 

In this example, we pipe the output of `curl` through `jq` (JSON query) to pretty-print the
JSON REST response:

<pre>
$ <b>curl --silent http://127.0.0.1:8100/hub/hank/mgmt/v1/status | jq</b>
{
  "name": "hank",
  "peer_clients": [
    {
      "client_name": "carol",
      "encryptor_names": [
        "sam"
      ],
      "local_pool": {
        "blocks": [
          {
            "uuid": "192c0144-ffec-4f95-9a9f-7d7a82310be7",
            "size": 2000,
            "data": "AAAAAAAAAAAAAA==...",
            "nr_used_bytes": 192,
            "nr_unused_bytes": 1808
          }
        ],
        "owner": "local"
      },
      "peer_pool": {
        "blocks": [
          {
            "uuid": "46627eb9-7e0d-4d40-8d67-8747f32a92f5",
            "size": 2000,
            "data": "AAAAAAAAAAAAAA==...",
            "nr_used_bytes": 288,
            "nr_unused_bytes": 1712
          }
        ],
        "owner": "peer"
      }
    },
    ...snip...
  }  
}
</pre>

Note 1: The `status` REST API is intended for debugging and understanding the protocol; it exposes
information that should not be exposed in a production environment.

Note 2: There is currently no authentication on any of the REST interfaces.
It is my understanding (but I could be wrong) that the DSKE protocol does not require the API
interfaces to be authenticated nor encrypted to be secure.
