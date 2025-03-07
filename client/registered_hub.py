"""
A registered DSKE hub.
"""


class RegisteredHub:
    """
    A registered DSKE hub.
    """

    _hub_name: str
    _pre_shared_key: bytes

    def __init__(self, hub_name: str, pre_shared_key: bytes):
        self._hub_name = hub_name
        self._pre_shared_key = pre_shared_key

    @property
    def pre_shared_key(self):
        """
        The pre-shared key.
        """
        return self._pre_shared_key
