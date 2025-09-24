# Getting started guide

## Installation

Clone the repository:

<pre>
git clone https://github.com/brunorijsman/dske-python.git
</pre>

Change directory to the cloned repository:

<pre>
cd dske-python
</pre>

We use Python 3.13 to develop and test the code.
Install Python 3.13 including venv(if needed):

<pre>
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get install python3.13
sudo apt-get install python3.13-venv
</pre>

Install pip (if needed):

<pre>
sudo apt-get install pip
</pre>

Create a virtual environment:

<pre>
python3.13 -m venv venv
</pre>

Activate the virtual environment:

<pre>
source venv/bin/activate
</pre>

Install de dependencies:

<pre>
pip install -r requirements.txt
</pre>