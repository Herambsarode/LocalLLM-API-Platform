import pytest
from unittest.mock import AsyncMock, patch
from app.core.security import (
    generate_api_key,
    hash_api_key,
    verify_api_key,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, LoginRequest
from app.database.models.user import User, UserRole


class TestSecurity:
    def test_generate_api_key_format(self):
        raw, hashed = generate_api_key()
        assert raw.startswith("sk_live_")
        assert len(raw) > 20
        assert len(hashed) == 64

    def test_hash_and_verify_api_key(self):
        raw, hashed = generate_api_key()
        assert verify_api_key(raw, hashed)
        assert not verify_api_key("wrong_key", hashed)

    def test_hash_and_verify_password(self):
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_create_and_decode_token(self):
        data = {"sub": "test-user-id", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded["sub"] == "test-user-id"
        assert decoded["role"] == "admin"

    def test_decode_invalid_token(self):
        assert decode_access_token("invalid_token") is None


@pytest.mark.asyncio
class TestAuthService:
    async def test_register_success(self, mock_db):
        user_service_mock = AsyncMock()
        user_service_mock.get_by_email.return_value = None
        mock_user = User(
            id="test-id",
            name="Test User",
            email="test@example.com",
            password_hash="hashed",
            role=UserRole.USER,
        )
        user_service_mock.create.return_value = mock_user

        with patch("app.services.auth_service.UserService", return_value=user_service_mock):
            service = AuthService(mock_db)
            result = await service.register(
                UserCreate(name="Test User", email="test@example.com", password="password123")
            )
            assert result.name == "Test User"
            assert result.email == "test@example.com"

    async def test_register_duplicate_email(self, mock_db):
        user_service_mock = AsyncMock()
        existing_user = User(
            id="existing-id",
            name="Existing",
            email="existing@example.com",
            password_hash="hash",
            role=UserRole.USER,
        )
        user_service_mock.get_by_email.return_value = existing_user

        with patch("app.services.auth_service.UserService", return_value=user_service_mock):
            service = AuthService(mock_db)
            with pytest.raises(ValueError, match="Email already registered"):
                await service.register(
                    UserCreate(name="Test", email="existing@example.com", password="password123")
                )

    async def test_login_invalid_credentials(self, mock_db):
        user_service_mock = AsyncMock()
        user_service_mock.get_by_email.return_value = None

        with patch("app.services.auth_service.UserService", return_value=user_service_mock):
            service = AuthService(mock_db)
            with pytest.raises(ValueError, match="Invalid email or password"):
                await service.login(
                    LoginRequest(email="nonexistent@example.com", password="password")
                )
