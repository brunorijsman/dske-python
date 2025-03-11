"""
A Pre-Shared Random Data (PSRD) allocation.
"""

from .fragment import Fragment


class Allocation:
    """
    A Pre-Shared Random Data (PSRD) allocation. A list of PSRD fragments.
    """

    _fragments: list[Fragment]

    def __init__(self, fragments: list[Fragment]):
        self._fragments = fragments

    def to_mgmt_dict(self) -> dict:
        """
        Get the management status.
        """
        return {
            "fragments": [fragment.to_mgmt_dict() for fragment in self._fragments],
        }
