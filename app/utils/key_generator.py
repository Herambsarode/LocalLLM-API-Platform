import secrets

from app.core.config import get_settings

settings = get_settings()


def generate_api_key() -> str:
    raw = secrets.token_hex(settings.api_key_bytes)
    return f"{settings.api_key_prefix}{raw}"
