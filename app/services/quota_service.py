import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.models.quota import Quota
from app.database.models.usage import UsageRecord
from app.core.config import get_settings

settings = get_settings()


class QuotaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_quota(self, user_id: uuid.UUID) -> Optional[Quota]:
        result = await self.db.execute(select(Quota).where(Quota.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_default_quota(self, user_id: uuid.UUID) -> Quota:
        quota = Quota(
            user_id=user_id,
            daily_requests_limit=settings.default_daily_requests,
            monthly_requests_limit=settings.default_monthly_requests,
            daily_tokens_limit=settings.default_daily_tokens,
            monthly_tokens_limit=settings.default_monthly_tokens,
        )
        self.db.add(quota)
        await self.db.flush()
        return quota

    async def update_quota(self, user_id: uuid.UUID, **kwargs) -> Optional[Quota]:
        quota = await self.get_quota(user_id)
        if not quota:
            return None
        for key, value in kwargs.items():
            if hasattr(quota, key):
                setattr(quota, key, value)
        await self.db.flush()
        return quota

    async def check_quota(self, user_id: uuid.UUID, estimated_tokens: int = 0) -> tuple[bool, str]:
        quota = await self.get_quota(user_id)
        if not quota:
            return False, "No quota assigned"

        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = day_start.replace(day=1)

        daily_usage = await self._get_usage_since(user_id, day_start)
        monthly_usage = await self._get_usage_since(user_id, month_start)

        if daily_usage["requests"] >= quota.daily_requests_limit:
            return False, "Daily request limit exceeded"
        if monthly_usage["requests"] >= quota.monthly_requests_limit:
            return False, "Monthly request limit exceeded"
        if daily_usage["tokens"] + estimated_tokens > quota.daily_tokens_limit:
            return False, "Daily token limit exceeded"
        if monthly_usage["tokens"] + estimated_tokens > quota.monthly_tokens_limit:
            return False, "Monthly token limit exceeded"

        return True, "OK"

    async def _get_usage_since(self, user_id: uuid.UUID, since: datetime) -> dict:
        query = select(
            func.coalesce(func.count(UsageRecord.id), 0),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0),
        ).where(
            UsageRecord.user_id == user_id,
            UsageRecord.created_at >= since,
        )
        result = await self.db.execute(query)
        row = result.one()
        return {"requests": row[0] or 0, "tokens": row[1] or 0}
