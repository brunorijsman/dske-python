"""
A peer DSKE client.
"""


class PeerClient:
    """
    A peer DSKE client.
    """

    _name: str
    _pre_shared_key: bytes

    def __init__(self, client_name: str, pre_shared_key: bytes):
        self._name = client_name
        self._pre_shared_key = pre_shared_key

    @property
    def pre_shared_key(self):
        """
        The pre-shared key.
        """
        return self._pre_shared_key
