"""
A PSRD allocation.
"""

import pydantic
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

    @property
    def fragments(self) -> list[Fragment] | None:
        """
        Get the fragments.
        """
        return self._fragments

    @property
    def data(self) -> bytes:
        """
        Get the data.
        """
        data = b""
        for fragment in self._fragments:
            assert not fragment.is_returned_to_block
            data += fragment.data
        return data

    def to_mgmt(self) -> dict:
        """
        Get the management status.
        """
        return {
            "fragments": [fragment.to_mgmt() for fragment in self._fragments],
        }

    def return_to_pool(self) -> None:
        """
        Return the allocation to the pool.
        """
        for fragment in self._fragments:
            fragment.return_to_block()
        self._fragments = []

    @classmethod
    def from_api(
        cls,
        api_allocation: APIAllocation,
        pool: "Pool",  # type: ignore
    ) -> "Allocation":
        """
        Create an Allocation from an APIAllocation.
        """
        try:
            fragments = []
            for api_fragment in api_allocation.fragments:
                fragment = Fragment.from_api(api_fragment, pool)
                fragments.append(fragment)
        except Exception as exc:
            for fragment in fragments:
                fragment.return_to_block()
            raise exc
        return Allocation(fragments=fragments)

    @classmethod
    def from_enc_str(
        cls,
        enc_str: str,
        pool: "Pool",  # type: ignore
    ) -> "Allocation":
        """
        Create an Allocation from an encoded string as used in an HTTP header or URL parameter.
        The format of the string is a comma-separated list of fragment encoded strings.
        """
        try:
            fragments = []
            for fragment_str in enc_str.split(","):
                fragment = Fragment.from_enc_str(fragment_str, pool)
                fragments.append(fragment)
        except Exception as exc:
            for fragment in fragments:
                fragment.return_to_block()
            raise exc
        return Allocation(fragments=fragments)

    def to_api(self) -> APIAllocation:
        """
        Create an APIAllocation from an Allocation.
        """
        return APIAllocation(
            fragments=[fragment.to_api() for fragment in self._fragments]
        )

    def to_enc_str(self) -> str:
        """
        Encode the Allocation as a string that can be used in HTTP headers or URL parameters.
        The format of the string is a comma-separated list of fragment encoded strings.
        """
        return ",".join([fragment.to_enc_str() for fragment in self._fragments])
