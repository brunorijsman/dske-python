"""
A PSRD allocation.
"""

import pydantic
from .common import bytes_to_str
from .fragment import APIFragment, Fragment


class APIAllocation(pydantic.BaseModel):
    """
    Representation of a PSRD allocation as used in API calls.
    """

    fragments: list[APIFragment]


class Allocation:
    """
    A PSRD allocation: a list of PSRD fragments.
    """

    _fragments: list[Fragment]

    def __init__(self, fragments: list[Fragment]):
        self._fragments = fragments
        self._value = None
        self._consumed = False

    @property
    def fragments(self) -> list[Fragment]:
        """
        Get the fragments.
        """
        return self._fragments

    @property
    def value(self) -> None | bytes:
        """
        Get the value.
        """
        return self._value

    def to_mgmt(self) -> dict:
        """
        Get the management status.
        """
        return {
            "fragments": [fragment.to_mgmt() for fragment in self._fragments],
            "value": bytes_to_str(self._value, truncate=True),
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

    @classmethod
    def from_api(
        cls,
        api_allocation: APIAllocation,
        pool: "Pool",  # type: ignore
    ) -> "Allocation":
        """
        Create an Allocation from an APIAllocation.
        """
        return Allocation(
            fragments=[
                Fragment.from_api(api_fragment, pool)
                for api_fragment in api_allocation.fragments
            ]
        )

    def to_api(self) -> APIAllocation:
        """
        Create an APIAllocation from an Allocation.
        """
        return APIAllocation(
            fragments=[fragment.to_api() for fragment in self._fragments]
        )
