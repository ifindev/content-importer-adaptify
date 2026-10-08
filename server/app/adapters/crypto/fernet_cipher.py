import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class FernetCredentialCipher:
    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Returns "" when the ciphertext doesn't decrypt with this key (it was
        encrypted under another CREDENTIAL_ENCRYPTION_KEY, or never set).
        WordPress then rejects an empty app password, so the site shows as
        unreachable instead of every request failing with a 500, and an empty
        review token makes the review link rotate."""
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            logger.warning("Stored secret doesn't decrypt with the current key")
            return ""
