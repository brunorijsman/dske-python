"""
DSKE Client Registration.
"""

class DSKEClientRegistration:
    """
    A Distributed Secure Key Exchange (DSKE) client registration.
    """
    _dske_secure_hub_name: str
    _dske_client_name: str
    _pre_shared_key: bytes

    def __init__(self, dske_secure_hub_name: str, dske_client_name: str, pre_shared_key: bytes):
        self._dske_secure_hub_name = dske_secure_hub_name
        self._dske_client_name = dske_client_name
        self._pre_shared_key = pre_shared_key
