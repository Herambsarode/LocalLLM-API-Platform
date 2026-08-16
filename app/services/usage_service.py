import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database.models.usage import UsageRecord
from app.schemas.usage import UsageRecordCreate, UsageSummary, UsageAnalytics


class UsageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_usage(self, data: UsageRecordCreate) -> UsageRecord:
        record = UsageRecord(**data.model_dump())
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_user_usage(
        self, user_id: uuid.UUID, page: int = 1, size: int = 20,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> tuple[list[UsageRecord], int]:
        query = select(UsageRecord).where(UsageRecord.user_id == user_id)
        count_query = select(func.count(UsageRecord.id)).where(UsageRecord.user_id == user_id)

        if start_date:
            query = query.where(UsageRecord.created_at >= start_date)
            count_query = count_query.where(UsageRecord.created_at >= start_date)
        if end_date:
            query = query.where(UsageRecord.created_at <= end_date)
            count_query = count_query.where(UsageRecord.created_at <= end_date)

        offset = (page - 1) * size
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        result = await self.db.execute(
            query.offset(offset).limit(size).order_by(UsageRecord.created_at.desc())
        )
        return list(result.scalars().all()), total

    async def get_user_summary(self, user_id: uuid.UUID, since: Optional[datetime] = None) -> UsageSummary:
        query = select(
            func.count(UsageRecord.id),
            func.coalesce(func.sum(UsageRecord.prompt_tokens), 0),
            func.coalesce(func.sum(UsageRecord.completion_tokens), 0),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0),
            func.coalesce(func.avg(UsageRecord.response_time_ms), 0),
        ).where(UsageRecord.user_id == user_id)

        if since:
            query = query.where(UsageRecord.created_at >= since)

        result = await self.db.execute(query)
        row = result.one()
        return UsageSummary(
            total_requests=row[0] or 0,
            total_prompt_tokens=row[1] or 0,
            total_completion_tokens=row[2] or 0,
            total_tokens=row[3] or 0,
            avg_response_time_ms=float(row[4] or 0),
        )

    async def get_user_daily_usage(self, user_id: uuid.UUID, days: int = 30) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = select(
            func.date_trunc("day", UsageRecord.created_at).label("day"),
            func.count(UsageRecord.id).label("requests"),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0).label("tokens"),
        ).where(
            and_(UsageRecord.user_id == user_id, UsageRecord.created_at >= since)
        ).group_by(func.date_trunc("day", UsageRecord.created_at)).order_by("day")

        result = await self.db.execute(query)
        return [
            {"date": str(row.day), "requests": row.requests, "tokens": row.tokens}
            for row in result.all()
        ]

    async def get_all_daily_usage(self, days: int = 30) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = select(
            func.date_trunc("day", UsageRecord.created_at).label("day"),
            func.count(UsageRecord.id).label("requests"),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0).label("tokens"),
        ).where(
            UsageRecord.created_at >= since
        ).group_by(func.date_trunc("day", UsageRecord.created_at)).order_by("day")

        result = await self.db.execute(query)
        return [
            {"date": str(row.day), "requests": row.requests, "tokens": row.tokens}
            for row in result.all()
        ]

    async def get_all_monthly_usage(self, months: int = 12) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=months * 30)
        query = select(
            func.date_trunc("month", UsageRecord.created_at).label("month"),
            func.count(UsageRecord.id).label("requests"),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0).label("tokens"),
        ).where(
            UsageRecord.created_at >= since
        ).group_by(func.date_trunc("month", UsageRecord.created_at)).order_by("month")

        result = await self.db.execute(query)
        return [
            {"date": str(row.month), "requests": row.requests, "tokens": row.tokens}
            for row in result.all()
        ]

    async def get_model_breakdown(self, user_id: Optional[uuid.UUID] = None, days: int = 30) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = select(
            UsageRecord.model,
            func.count(UsageRecord.id).label("requests"),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0).label("tokens"),
        ).where(UsageRecord.created_at >= since)

        if user_id:
            query = query.where(UsageRecord.user_id == user_id)

        query = query.group_by(UsageRecord.model).order_by(func.count(UsageRecord.id).desc())

        result = await self.db.execute(query)
        return [
            {"model": row.model, "requests": row.requests, "tokens": row.tokens}
            for row in result.all()
        ]

    async def get_global_stats(self) -> dict:
        query = select(
            func.count(UsageRecord.id),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0),
        )
        result = await self.db.execute(query)
        row = result.one()
        return {
            "total_requests": row[0] or 0,
            "total_tokens": row[1] or 0,
        }
