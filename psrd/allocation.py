"""
A Pre-Shared Random Data (PSRD) allocation.
"""

import common

from .fragment import Fragment


class Allocation:
    """
    A Pre-Shared Random Data (PSRD) allocation. A list of PSRD fragments.
    """

    _fragments: list[Fragment]

    def __init__(self, fragments: list[Fragment]):
        self._fragments = fragments
        self._value = None
        self._consumed = False

    def to_mgmt_dict(self) -> dict:
        """
        Get the management status.
        """
        return {
            "fragments": [fragment.to_mgmt_dict() for fragment in self._fragments],
            "value": common.bytes_to_str(self._value, truncate=True),
            "consumed": self._consumed,
        }

    def consume(self) -> bytes:
        """
        Consume the PSRD allocation. This requires that the allocation was previously allocated.
        Since the allocation was successful, consuming the data cannot fail. Once the data has
        consumed, it cannot be un-consumed.
        """
        assert not self._consumed
        assert self._value is None
        self._value = b""
        for fragment in self._fragments:
            self._value += fragment.consume()
        self._consumed = True
        return self._value
