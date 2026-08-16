import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.api_key_service import APIKeyService
from app.schemas.api_key import APIKeyCreate
from app.database.models.api_key import APIKey


@pytest.mark.asyncio
class TestAPIKeyService:
    async def test_create_api_key(self, mock_db):
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        service = APIKeyService(mock_db)
        user_id = uuid.uuid4()
        key_obj, raw_key = await service.create(
            user_id, APIKeyCreate(name="Test Key")
        )

        assert raw_key.startswith("sk_live_")
        assert key_obj.user_id == user_id
        assert key_obj.name == "Test Key"

    async def test_validate_valid_key(self, mock_db):
        service = APIKeyService(mock_db)
        user_id = uuid.uuid4()

        from app.core.security import generate_api_key, hash_api_key
        raw, hashed = generate_api_key()

        mock_key = APIKey(
            id=uuid.uuid4(),
            user_id=user_id,
            key_prefix=raw[:20],
            key_hash=hashed,
            is_active=True,
            expires_at=None,
            usage_count=0,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_key
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        result = await service.validate_api_key(raw)
        assert result is not None
        assert result.user_id == user_id

    async def test_validate_invalid_key(self, mock_db):
        service = APIKeyService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.validate_api_key("sk_live_invalid_key")
        assert result is None

    async def test_rotate_key(self, mock_db):
        service = APIKeyService(mock_db)
        key_id = uuid.uuid4()
        user_id = uuid.uuid4()

        old_key = APIKey(
            id=key_id,
            user_id=user_id,
            key_prefix="sk_live_old_",
            key_hash="old_hash",
            is_active=True,
            usage_count=5,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = old_key
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        updated, raw_key = await service.rotate(key_id)
        assert updated is not None
        assert raw_key is not None
        assert raw_key.startswith("sk_live_")
        assert updated.key_hash != "old_hash"
