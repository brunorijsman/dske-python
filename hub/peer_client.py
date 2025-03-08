"""
A peer DSKE client.
"""

import base64


class PeerClient:
    """
    A peer DSKE client.
    """

    _client_name: str
    _pre_shared_key: bytes

    def __init__(self, client_name: str, pre_shared_key: bytes):
        self._client_name = client_name
        self._pre_shared_key = pre_shared_key

    def management_status(self):
        """
        Get the management status.
        """
        encoded_pre_shared_key = base64.b64encode(self._pre_shared_key).decode("utf-8")
        return {
            "client_name": self._client_name,
            # TODO: Should not report this; include it for now only for debugging
            "pre_shared_key": encoded_pre_shared_key,
        }

    @property
    def pre_shared_key(self):
        """
        The pre-shared key.
        """
        return self._pre_shared_key
