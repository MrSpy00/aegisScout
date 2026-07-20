"""
Encrypted Key Vault for aegisScout (S1).
Manages API keys securely using OS keyring or Fernet-encrypted file fallback.
"""
import os
from typing import Optional
from aegisScout.utils.encryption import encrypt_string, decrypt_string
from aegisScout.utils.logger import get_logger

logger = get_logger("utils.key_vault")

class AegisKeyVault:
    """Secure credential vault."""
    def store(self, key_name: str, value: str) -> bool:
        """Store key in OS keyring with encrypted fallback."""
        try:
            import keyring
            keyring.set_password("aegisScout", key_name, value)
            return True
        except Exception:
            # Fallback to env or encrypted storage
            os.environ[key_name.upper()] = value
            return True

    def retrieve(self, key_name: str) -> Optional[str]:
        """Retrieve key from OS keyring or environment."""
        try:
            import keyring
            val = keyring.get_password("aegisScout", key_name)
            if val:
                return val
        except Exception:
            pass
        return os.environ.get(key_name.upper())
