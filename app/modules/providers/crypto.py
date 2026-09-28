"""Enkripsi kredensial produk AI. SCRUM-114.

decrypt hanya untuk worker dan uji koneksi. Jangan panggil dari
serializer response: plaintext tidak boleh keluar lewat HTTP.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.shared.config import get_settings


class CredentialError(Exception):
    """Kunci hilang, kunci rusak, atau ciphertext tidak bisa dibuka."""


def credential_hint(plaintext: str) -> str:
    if len(plaintext) < 4:
        raise CredentialError("credential must be at least 4 characters")
    return plaintext[-4:]


def encrypt_credential(plaintext: str) -> bytes:
    credential_hint(plaintext)
    raw = get_settings().credential_encryption_key.strip()
    if not raw:
        raise CredentialError("credential encryption key is not configured")
    try:
        fernet = Fernet(raw.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise CredentialError("credential encryption key is invalid") from exc
    return fernet.encrypt(plaintext.encode("utf-8"))


def decrypt_credential(ciphertext: bytes) -> str:
    raw = get_settings().credential_encryption_key.strip()
    if not raw:
        raise CredentialError("credential encryption key is not configured")
    try:
        fernet = Fernet(raw.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise CredentialError("credential encryption key is invalid") from exc
    try:
        return fernet.decrypt(ciphertext).decode("utf-8")
    except InvalidToken as exc:
        raise CredentialError("credential ciphertext could not be decrypted") from exc
