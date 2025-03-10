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
