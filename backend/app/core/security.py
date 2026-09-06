import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"

# PBKDF2-HMAC-SHA256 work factor. OWASP's 2023 floor is 600k iterations.
# Stored hashes carry their own iteration count so this can be raised later
# without invalidating existing passwords.
PBKDF2_ITERATIONS = 600_000
_HASH_SCHEME = "pbkdf2_sha256"


def get_password_hash(password: str) -> str:
    """Returns 'pbkdf2_sha256$<iterations>$<salt>$<hex key>'."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    )
    return f"{_HASH_SCHEME}${PBKDF2_ITERATIONS}${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Constant-time verification. Understands both the current format and the
    legacy '<salt>$<hex key>' 100k-iteration format so old rows keep working.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) == 4 and parts[0] == _HASH_SCHEME:
            iterations, salt, key_hex = int(parts[1]), parts[2], parts[3]
        elif len(parts) == 2:  # legacy
            iterations, (salt, key_hex) = 100_000, parts
        else:
            return False

        check_key = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), iterations
        )
        return secrets.compare_digest(check_key.hex(), key_hex)
    except (ValueError, TypeError):
        return False


def needs_rehash(hashed_password: str) -> bool:
    """True when a stored hash uses an outdated scheme or work factor."""
    parts = hashed_password.split("$")
    if len(parts) != 4 or parts[0] != _HASH_SCHEME:
        return True
    try:
        return int(parts[1]) < PBKDF2_ITERATIONS
    except ValueError:
        return True


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[int]:
    """
    Returns the user id encoded in a valid token, or None. Signature and
    expiry are enforced by python-jose; the algorithm is pinned so a token
    cannot downgrade itself to 'none'.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            return None
        return int(subject)
    except (JWTError, ValueError, TypeError):
        return None
