import hashlib
import secrets

import bcrypt


def hash_password(password: str) -> str:
    passwd = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(passwd, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    passwd = plain_password.encode("utf-8")
    hashed = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(passwd, hashed)
    except Exception:
        return False


def generate_reset_code() -> str:
    return f"{secrets.randbelow(10**6):06d}"


def hash_reset_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()
