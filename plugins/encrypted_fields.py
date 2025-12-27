import base64
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


def get_encryption_key():
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    if not key:
        raise ValueError(
            "ENCRYPTION_KEY not found in settings. "
            "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    if isinstance(key, str):
        key = key.encode()
    return key


class EncryptedTextField(models.TextField):
    def get_prep_value(self, value):
        if value is None or value == '':
            return value

        fernet = Fernet(get_encryption_key())
        if isinstance(value, str):
            value = value.encode()
        encrypted = fernet.encrypt(value)
        return base64.b64encode(encrypted).decode('utf-8')

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value

        try:
            fernet = Fernet(get_encryption_key())
            encrypted_bytes = base64.b64decode(value.encode('utf-8'))
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception:
            return value


class EncryptedCharField(models.CharField):
    def get_prep_value(self, value):
        if value is None or value == '':
            return value

        fernet = Fernet(get_encryption_key())
        if isinstance(value, str):
            value = value.encode()
        encrypted = fernet.encrypt(value)
        return base64.b64encode(encrypted).decode('utf-8')

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value

        try:
            fernet = Fernet(get_encryption_key())
            encrypted_bytes = base64.b64decode(value.encode('utf-8'))
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception:
            return value
