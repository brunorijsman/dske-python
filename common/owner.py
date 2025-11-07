"""
Enumeration for pool ownership.
"""

import enum
from .exceptions import InvalidOwnerError


class Owner(enum.Enum):
    """
    Who owns a pool? The client node or the hub node? Only the owner is allowed to make
    allocations out of the pool. The non-owner only takes data out of the pool, but the peer
    decides which data is taken (i.e. the peer does the allocation).
    """

    LOCAL = 1
    PEER = 2

    def __str__(self):
        return self.to_str()

    def to_str(self, local_name: str = "local", peer_name: str = "peer") -> str:
        """
        Convert the Owner to a string.
        """
        match self:
            case Owner.LOCAL:
                return local_name
            case Owner.PEER:
                return peer_name

    @staticmethod
    def from_str(
        owner_str: str, local_name: str = "local", peer_name: str = "peer"
    ) -> "Owner":
        """
        Create an Owner from a string.
        """
        lower_owner_str = owner_str.lower()
        if lower_owner_str == local_name:
            return Owner.LOCAL
        if lower_owner_str == peer_name:
            return Owner.PEER
        raise InvalidOwnerError(owner_str)
