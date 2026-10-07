from cryptography.fernet import Fernet

from app.adapters.crypto.fernet_cipher import FernetCredentialCipher

KEY = Fernet.generate_key().decode()


def test_encrypt_then_decrypt_round_trips():
    cipher = FernetCredentialCipher(KEY)
    ciphertext = cipher.encrypt("super-secret-app-password")
    assert ciphertext != "super-secret-app-password"
    assert cipher.decrypt(ciphertext) == "super-secret-app-password"


def test_encrypting_the_same_plaintext_twice_gives_different_ciphertext():
    cipher = FernetCredentialCipher(KEY)
    first = cipher.encrypt("same-password")
    second = cipher.encrypt("same-password")
    assert first != second
    assert cipher.decrypt(first) == cipher.decrypt(second) == "same-password"
