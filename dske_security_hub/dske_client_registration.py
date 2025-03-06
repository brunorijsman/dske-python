"""
DSKE Client Registration.
"""

from uuid import UUID

class DSKEClientRegistration:
    """
    A Distributed Secure Key Exchange (DSKE) client registration.
    """
    _dske_secure_hub_uuid: UUID
    _dske_client_uuid: UUID
    _pre_shared_key: bytes

    def __init__(self, dske_secure_hub_uuid: UUID, dske_client_uuid: UUID, pre_shared_key: bytes):
        self._dske_secure_hub_uuid = dske_secure_hub_uuid
        self._dske_client_uuid = dske_client_uuid
        self._pre_shared_key = pre_shared_key
