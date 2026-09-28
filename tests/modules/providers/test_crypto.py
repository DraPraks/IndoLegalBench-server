"""SCRUM-75 SCRUM-114: credential encryption fails closed.

The helper is the only place that turns a product credential into stored
bytes. These tests lock the rules SCRUM-115 and SCRUM-116 will rely on:
Fernet round-trip, a 4-character hint, and a hard failure when the key
is missing, invalid, or does not match the ciphertext.
"""

import pytest
from cryptography.fernet import Fernet

from app.modules.providers.crypto import (
    CredentialError,
    credential_hint,
    decrypt_credential,
    encrypt_credential,
)
from app.shared.config import get_settings


@pytest.fixture
def encryption_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", key)
    get_settings.cache_clear()
    yield key
    get_settings.cache_clear()


def test_encrypt_then_decrypt_returns_the_plaintext(encryption_key):
    plaintext = "provider-token-value-7kPq"
    token = encrypt_credential(plaintext)

    assert decrypt_credential(token) == plaintext


def test_ciphertext_does_not_contain_the_plaintext(encryption_key):
    plaintext = "provider-token-value-7kPq"
    token = encrypt_credential(plaintext)

    assert plaintext.encode() not in token


def test_the_same_secret_encrypts_to_different_tokens(encryption_key):
    plaintext = "provider-token-value-7kPq"

    assert encrypt_credential(plaintext) != encrypt_credential(plaintext)


def test_hint_is_the_last_four_characters():
    assert credential_hint("provider-token-value-7kPq") == "7kPq"


def test_secret_shorter_than_four_characters_is_rejected(encryption_key):
    with pytest.raises(CredentialError):
        credential_hint("abc")
    with pytest.raises(CredentialError):
        encrypt_credential("abc")


def test_missing_key_is_rejected(monkeypatch):
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", "")
    get_settings.cache_clear()

    with pytest.raises(CredentialError):
        encrypt_credential("provider-token-value-7kPq")


def test_invalid_key_is_rejected(monkeypatch):
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", "not-a-fernet-key")
    get_settings.cache_clear()

    with pytest.raises(CredentialError):
        encrypt_credential("provider-token-value-7kPq")


def test_decrypt_with_the_wrong_key_is_rejected(encryption_key, monkeypatch):
    token = encrypt_credential("provider-token-value-7kPq")
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", Fernet.generate_key().decode())
    get_settings.cache_clear()

    with pytest.raises(CredentialError):
        decrypt_credential(token)


def test_tampered_ciphertext_is_rejected(encryption_key):
    token = bytearray(encrypt_credential("provider-token-value-7kPq"))
    token[0] ^= 0xFF

    with pytest.raises(CredentialError):
        decrypt_credential(bytes(token))
