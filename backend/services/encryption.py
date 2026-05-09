import os
from cryptography.fernet import Fernet

KEY_FILE = "backend/keys/backup.key"

def generate_key():
    if not os.path.exists(KEY_FILE):
        os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        os.chmod(KEY_FILE, 0o600)

def _get_fernet():
    if not os.path.exists(KEY_FILE):
        generate_key()
    with open(KEY_FILE, "rb") as f:
        key = f.read()
    return Fernet(key)

def encrypt_file(data: bytes) -> bytes:
    f = _get_fernet()
    return f.encrypt(data)

def decrypt_file(data: bytes) -> bytes:
    f = _get_fernet()
    return f.decrypt(data)
