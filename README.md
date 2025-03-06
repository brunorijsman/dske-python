# dske-python

This repository contains an implementation of Distributed Symmetric Key Establishment (DSKE) as specified in IETF draft
[draft-mwag-dske-01](https://datatracker.ietf.org/doc/draft-mwag-dske/01/).
The code is implemented in Python 3.12 and uses FastAPI.

**WARNING**: This project is in the extremely early stages of implementation and nowhere near usable yet.

To start the DSKE security hub:

```pyton
cd dske_hub
fastapi dev main.py
```

For DSKE security hub API, open URL `http://127.0.0.1:8000/docs` in a browser.
