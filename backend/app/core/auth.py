from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta
from logging import getLogger, ERROR
from pathlib import Path
from secrets import token_hex
from typing import Any

from cryptography.fernet import Fernet
from jose import jwt
from passlib.context import CryptContext

from app.core.config import CONFIG_ROOT, config
from app.logging.logger import log


"""File where the private key is stored"""
if config.IS_DOCKER:
    KEY_FILE = Path('/config/.key.txt')
else:
    KEY_FILE = CONFIG_ROOT / '.key.txt'

"""Only log passlib errors so that bcrypt.__version__ boot warning is ignored"""
getLogger('passlib').setLevel(ERROR)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def generate_secret_key() -> bytes:
    """
    Generate a new, random secret.

    Returns:
        A 16-character random hexstring.
    """

    return urlsafe_b64encode(token_hex(16).encode())


def verify_password(plaintext: str, hashed: str) -> bool:
    """
    Verify the given plaintext against the given hashed password.

    Args:
        plaintext: The plaintext password to verify.
        hashed: Hashstring to compare to.

    Returns:
        True if the hash of `plaintext` matches `hatched`. False
        otherwise.
    """

    return pwd_context.verify(plaintext, hashed)


def get_secret_key() -> bytes:
    """
    Get the secret key for all encryption. This reads the local key file
    if it exists, and generates a new one if it does not.

    Returns:
        Secret key (as a hexstring).
    """

    # File exists, read
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()

    # No file, generate and write new key
    key = generate_secret_key()
    KEY_FILE.write_bytes(key)
    log.info(f'Generated encrpytion key - wrote to "{KEY_FILE}"')

    return key


def get_password_hash(password: str) -> str:
    """
    Hash the given plaintext password.

    Args:
        password: The plaintext password to hash.

    Returns:
        The hash of `password`.
    """

    return pwd_context.hash(password)


def create_access_token(
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
    """
    Create an encoded JWT with the given data.

    Args:
        data: Data to encode in the JWT.
        expires_delta: How long the token is valid for. If not provided,
            the token is valid for 7 days.

    Returns:
        JWT string of the encoded data and expiration date.
    """

    expires = datetime.now(UTC) + (expires_delta or timedelta(days=7))
    to_encode = data.copy()
    to_encode.update({'exp': expires})

    return jwt.encode(
        to_encode,
        get_secret_key(),
        algorithm=config.CRYPTO_ALGORITHM
    )


def encrypt(plaintext: str) -> str:
    """
    Encrypt the given plaintext.

    Args:
        plaintext: Text to encrypt.

    Returns:
        Encrypted text.
    """

    return Fernet(get_secret_key()).encrypt(plaintext.encode()).decode()


def decrypt(encrypted_text: str) -> str:    
    """
    Decrypt the given encrypted text into plaintext.

    Args:
        encrypted_text: Text to decrypt.

    Returns:
        Plain decrypted text.
    """

    return Fernet(get_secret_key()).decrypt(encrypted_text).decode()


__all__ = (
    'create_access_token',
    'decrypt',
    'encrypt',
    'generate_secret_key',
    'get_password_hash',
    'verify_password',
)
