"""
A Pre-Shared Random Data (PSRD) block.
"""

import base64
from uuid import UUID, uuid4
from os import urandom
from pydantic import PositiveInt


class PSRDBlock:
    """
    A Pre-Shared Random Data (PSRD) block.
    """

    _uuid: UUID
    _original_size: int
    _remaining_size: int
    _data: bytes

    def __init__(self, uuid: UUID, data: bytes):
        self._uuid = uuid
        # TODO: Do we need original size? Isn't this just the size of the data field?
        self._original_size = len(data)
        self._remaining_size = self._original_size
        self._data = data

    @property
    def uuid(self):
        """
        The UUID of the PSRD block.
        """
        return self._uuid

    @property
    def remaining_size(self):
        """
        The remaining number of bytes that have not yet been consumed.
        """
        return self._remaining_size

    def to_protocol_json(self):
        """
        Get a JSON representation of the PSRD block, for the purpose of sending it in a protocol
        message.
        """
        encoded_data = base64.b64encode(self._data).decode("utf-8")
        return {
            "uuid": self._uuid,
            "data": encoded_data,
        }

    def management_status(self):
        """
        Get a JSON representation of the PSRD block, for the purpose of sending it in a protocol
        message.
        """
        encoded_data = base64.b64encode(self._data).decode("utf-8")
        # TODO: Truncate data with "..." if longer than some length
        return {
            "uuid": self._uuid,
            "original_size": self._original_size,
            "remaining_size": self._remaining_size,
            "data": encoded_data,
        }

    @classmethod
    def from_protocol_json(cls, json):
        """
        Create a PSRD block from the JSON representation.
        """
        # TODO: Error handling
        uuid = json["uuid"]
        encoded_data = json["data"]
        data = base64.b64decode(encoded_data.encode("utf-8"))
        return PSRDBlock(uuid, data)

    @classmethod
    def create_random_psrd_block(cls, size: PositiveInt):
        """
        Create a PSRD block, containing `size` random bytes.
        """
        uuid = uuid4()
        data = urandom(size)
        return PSRDBlock(uuid, data)
