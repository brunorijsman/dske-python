"""
A DSKE client.
"""

class DSKEClient:
    """
    A DSKE client.
    """
    _dske_client_name: str
    _pre_shared_key: bytes

    def __init__(self, dske_client_name: str, pre_shared_key: bytes):
        self._dske_client_name = dske_client_name
        self._pre_shared_key = pre_shared_key

    @property
    def pre_shared_key(self):
        """
        The pre-shared key.
        """
        return self._pre_shared_key