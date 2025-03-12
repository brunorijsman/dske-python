# Distributed Symmetric Key Establishment (DSKE)

Distributed Symmetric Key Establishment (DSKE) is a method for parties to agree on a shared secret
(typically a symmetric encryption key) in a quantum-safe manner.

It is sometimes also referred to by other names, including Symmetric Key Agreement (SKA).

DSKE is described in detail in the following arXiv papers:

 * arXiv:2205.00615 
 [Distributed Symmetric Key Establishment: A scalable, quantum-proof key distribution system](https://arxiv.org/abs/2205.00615)

 * 	arXiv:2304.13789 
 [Composable Security of Distributed Symmetric Key Establishment Protocol](https://arxiv.org/abs/2304.13789)


# dske-python

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
