# Developer guide

## Technology stack

Our technology stack is:
* [Python 3.13](https://www.python.org/) as the programming language.
* [FastAPI](https://www.python.org/) for HTTP APIs.
* [Git](https://git-scm.com/) and [Github](https://github.com/brunorijsman/dske-python) for version control.
* [Github actions](https://github.com/features/actions) for continuous integration.
* [Pylint](https://pypi.org/project/pylint/) for linting.
* [Black](https://black.readthedocs.io/) for code formatting.
* [Coverage](https://coverage.readthedocs.io/) for code coverage.
* [Pip](https://pypi.org/project/pip/) for dependency management.
* [Venv](https://docs.python.org/3/library/venv.html) for virtual environments.

## DSKE protocol

The Distributed Symmetric Key Establishment (DSKE) implementation in this repository is based on
IETF draft
[draft-mwag-dske-02](https://datatracker.ietf.org/doc/draft-mwag-dske/02/).
It has been developed completely independently of the authors of the draft, based only on the public
information in the draft.
See [the DSKE protocol page](/docs/dske-protocol.md) for more details.

## Proof of concept

The code is intended to be a proof-of-concept to study the DSKE protocol; it is not
suitable for  production deployments for numerous reasons (e.g. we have made no effort to prevent
side-channel attacks).

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