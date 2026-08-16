import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate
from app.core.security import generate_api_key, hash_api_key


class APIKeyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: uuid.UUID, data: APIKeyCreate) -> tuple[APIKey, str]:
        raw_key, hashed_key = generate_api_key()
        key_prefix = raw_key[:20]

        api_key = APIKey(
            user_id=user_id,
            key_prefix=key_prefix,
            key_hash=hashed_key,
            name=data.name,
            expires_at=data.expires_at,
        )
        self.db.add(api_key)
        await self.db.flush()
        return api_key, raw_key

    async def get_by_id(self, key_id: uuid.UUID) -> Optional[APIKey]:
        result = await self.db.execute(select(APIKey).where(APIKey.id == key_id))
        return result.scalar_one_or_none()

    async def get_by_key_hash(self, key_hash: str) -> Optional[APIKey]:
        result = await self.db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
        return result.scalar_one_or_none()

    async def validate_api_key(self, raw_key: str) -> Optional[APIKey]:
        hashed = hash_api_key(raw_key)
        api_key = await self.get_by_key_hash(hashed)
        if not api_key:
            return None
        if not api_key.is_active:
            return None
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            return None
        api_key.last_used_at = datetime.now(timezone.utc)
        api_key.usage_count += 1
        await self.db.flush()
        return api_key

    async def get_user_keys(self, user_id: uuid.UUID, page: int = 1, size: int = 20) -> tuple[list[APIKey], int]:
        offset = (page - 1) * size
        count_result = await self.db.execute(
            select(func.count(APIKey.id)).where(APIKey.user_id == user_id)
        )
        total = count_result.scalar() or 0
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id)
            .offset(offset)
            .limit(size)
            .order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all()), total

    async def update(self, key_id: uuid.UUID, data: APIKeyUpdate) -> Optional[APIKey]:
        api_key = await self.get_by_id(key_id)
        if not api_key:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(api_key, key, value)
        await self.db.flush()
        return api_key

    async def delete(self, key_id: uuid.UUID) -> bool:
        api_key = await self.get_by_id(key_id)
        if not api_key:
            return False
        await self.db.delete(api_key)
        await self.db.flush()
        return True

    async def rotate(self, key_id: uuid.UUID) -> tuple[Optional[APIKey], Optional[str]]:
        api_key = await self.get_by_id(key_id)
        if not api_key:
            return None, None
        raw_key, hashed_key = generate_api_key()
        api_key.key_hash = hashed_key
        api_key.key_prefix = raw_key[:20]
        await self.db.flush()
        return api_key, raw_key
