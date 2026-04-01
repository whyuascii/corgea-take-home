import base64

from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from django.conf import settings
from django.db import models

_fernet_cache = None


def _derive_fernet_key(raw_key):
    """Derive a 32-byte Fernet key from a raw secret using HKDF-SHA256."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"vulntracker-field-encryption",
        info=b"fernet-key",
    )
    derived = hkdf.derive(raw_key.encode())
    return base64.urlsafe_b64encode(derived)


def _get_fernet():
    """Build a MultiFernet from FIELD_ENCRYPTION_KEY(S).

    Supports key rotation: set FIELD_ENCRYPTION_KEYS to a comma-separated
    list of keys.  The first key encrypts new data; all keys can decrypt.
    Falls back to the single FIELD_ENCRYPTION_KEY for non-rotation setups.
    """
    global _fernet_cache
    if _fernet_cache is not None:
        return _fernet_cache

    keys_csv = getattr(settings, "FIELD_ENCRYPTION_KEYS", "")
    if keys_csv:
        raw_keys = [k.strip() for k in keys_csv.split(",") if k.strip()]
    else:
        raw_keys = [settings.FIELD_ENCRYPTION_KEY]

    fernets = [Fernet(_derive_fernet_key(k)) for k in raw_keys]
    _fernet_cache = MultiFernet(fernets)
    return _fernet_cache


class EncryptedTextField(models.TextField):
    """TextField that encrypts values at rest using Fernet (AES-128-CBC + HMAC)"""

    def get_prep_value(self, value):
        """Encrypt the value before storing in the database."""
        value = super().get_prep_value(value)
        if not value:
            return value
        return _get_fernet().encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        """Decrypt the value when reading from the database."""
        if not value:
            return value
        return _get_fernet().decrypt(value.encode()).decode()

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, "core.fields.EncryptedTextField", args, kwargs
