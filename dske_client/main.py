"""
Main module for a DSKE client.
"""

from base64 import b64encode
from fastapi import FastAPI
from pydantic import PositiveInt

APP = FastAPI()
