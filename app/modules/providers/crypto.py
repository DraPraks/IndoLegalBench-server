"""Encrypt an AI product credential. SCRUM-114.

decrypt is for the measurement worker and the connection test only.
Do not call it from a response serializer. No endpoint returns the plaintext.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.shared.config import get_settings

HINT_LENGTH = 4


class CredentialError(Exception):
    """Missing key, invalid key, or ciphertext that cannot be opened."""


def credential_hint(plaintext: str) -> str:
    if len(plaintext) < HINT_LENGTH:
        raise CredentialError("credential must be at least 4 characters")
    return plaintext[-HINT_LENGTH:]


def encrypt_credential(plaintext: str) -> bytes:
    credential_hint(plaintext)
    return _fernet().encrypt(plaintext.encode("utf-8"))


def decrypt_credential(ciphertext: bytes) -> str:
    try:
        return _fernet().decrypt(ciphertext).decode("utf-8")
    except InvalidToken as exc:
        raise CredentialError("credential ciphertext could not be decrypted") from exc


def _fernet() -> Fernet:
    raw = get_settings().credential_encryption_key.strip()
    if not raw:
        raise CredentialError("credential encryption key is not configured")
    try:
        return Fernet(raw.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise CredentialError("credential encryption key is invalid") from exc
