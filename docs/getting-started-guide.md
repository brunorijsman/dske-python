# Getting started guide

## Installation

Clone the repository:

```
git clone https://github.com/brunorijsman/dske-python.git
```

Change directory to the cloned repository:

```
cd dske-python
```

We use Python 3.13 to develop and test the code.
Install Python 3.13 including venv (if needed):

```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get install python3.13
sudo apt-get install python3.13-venv
```

Install pip (if needed):

```
sudo apt-get install pip
```

Create a virtual environment:

```
python3.13 -m venv venv
```

Activate the virtual environment:

```
source venv/bin/activate
```

Install de dependencies:

```
pip install -r requirements.txt
```

## The example topology

View the example topology file `topology.yaml`:

```
$ cat topology.yaml
hubs:
  - name: hank
  - name: helen
  - name: hilary
  - name: holly
  - name: hugo
clients:
  - name: carol
  - name: celia
  - name: cindy
  - name: connie
  - name: curtis
```

## The `manager.py` script

The `manager.py` is used to manage topologies.
Use the `--help` option to see how it is used:

```
$ ./manager.py topology.yaml --help
usage: manager.py [-h] [--client CLIENT | --hub HUB] configfile {start,stop,status,etsi-qkd} ...

DSKE Manager

positional arguments:
  configfile            Configuration filename
  {start,stop,status,etsi-qkd}
    start               Start all hubs and clients
    stop                Stop all hubs and clients
    status              Report status for all hubs and clients
    etsi-qkd            ETSI QKD operations

options:
  -h, --help            show this help message and exit
  --client CLIENT       Filter on client name
  --hub HUB             Filter on hub name
```

## Start WireShark

Optionally, if
[WireShark](https://www.wireshark.org/)
is installed on your computer, start it now so that you can view the protocol in action.
Start a capture on loopback interface `lo0` and filter on HTTP messages.

![Wireshark started)](/docs/figures/wireshark-started.png)

## Start the example topology

Use the `manager.py` script to start the topology:

```
$ ./manager.py topology.yaml start
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
```

## Explore the Swagger documentation

You can explore the Swagger documentation for the interface for each node using a browser.
Each node (i.e. each client and each hub) runs in a separate process and is listening
on a separate HTTP port as reported in the output when the topology was started.
For example, hub hank is listening on HTTP port 8100.
To view the Swagger API documentation for hub hank open a browser and go to URL
`http://localhost:8100/docs`

![Swagger documentation for hub hank](/docs/figures/swagger-docs.png)

## Create key pair between clients Carol and Connie

Use the `manager.py` script to create a key pair between clients Carol and Connie using the
ETSI QKD 014 interface.
You will get different key IDs and key values, but they should match.


```
$ ./manager.py topology.yaml etsi-qkd carol connie get-key-pair
Invoke ETSI QKD Get Key API for client carol on port 8105
{
  "keys": {
    "key_ID": "565a2f78-b2ab-4494-b87b-11a49a3dc4a4",
    "key": "+andEzVzqw3TKBf8QwSy9A=="
  }
}
Invoke ETSI QKD Get Key with Key IDs API for client connie on port 8108
{
  "keys": [
    {
      "key_ID": "565a2f78-b2ab-4494-b87b-11a49a3dc4a4",
      "key": "+andEzVzqw3TKBf8QwSy9A=="
    }
  ]
}
Key values match
```

## Explore the protocol messages in WireShark

You can explore the protocol messages in WireShark:
The protocol is explained in the [protocol guide](/docs/protocol-guide.md).

![Wireshark trace)](/docs/figures/wireshark-trace.png)

## Display the internal state of a node

Use the `manager.py` script to view the internal state of a node, in this case client carol:

```
$ ./manager.py topology.yaml --client carol status
Status for client carol on port 8105
{
  "name": "carol",
  "peer_hubs": [
    {
      "hub_name": "hank",
      "registered": true,
      "local_pool": {
        "blocks": [
          {
            "uuid": "7b5edbb0-e51d-49b6-9e87-99f684df6180",
            "size": 1000,
            "data": "AAAAAAAAAAAAAA==...",
            "allocated": 48,
            "consumed": 48
          }
        ],
        "owner": "Owner.LOCAL"
      },
      "peer_pool": {
        "blocks": [
          {
            "uuid": "b9654256-403b-470f-abab-c47901a5bb82",
            "size": 1000,
            "data": "AAAAAAAAAAAAAA==...",
            "allocated": 32,
            "consumed": 32
          }
        ],
        "owner": "Owner.PEER"
      }
    },
    ...
  ]
}
```

## Stop the topology

Use the `manager.py` script to stop the topology:

```
$ ./manager.py topology.yaml stop
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
```

## View the `.out` file for a node:

View the `.out` file for a node, in this example client Carol.
It contains logs and debugging information.
Your output may look different.

```
$ cat client-carol.out
INFO:     Started server process [63929]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8105 (Press CTRL+C to quit)
INFO:     127.0.0.1:54108 - "POST /client/carol/mgmt/v1/stop HTTP/1.1" 200 OK
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [63929]
INFO:     Started server process [73470]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8105 (Press CTRL+C to quit)
INFO:     127.0.0.1:54466 - "GET /client/carol/etsi/api/v1/keys/connie/enc_keys HTTP/1.1" 200 OK
INFO:     127.0.0.1:54611 - "GET /client/carol/mgmt/v1/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54625 - "POST /client/carol/mgmt/v1/stop HTTP/1.1" 200 OK
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [73470]
```