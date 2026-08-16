import hashlib

from app.core.config import get_settings

settings = get_settings()


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed: str) -> bool:
    return hash_api_key(api_key) == hashed
