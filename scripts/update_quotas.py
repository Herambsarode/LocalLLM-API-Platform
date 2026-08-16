"""Apply configured default quotas to existing users."""

import asyncio

from sqlalchemy import update

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.database.models.quota import Quota


async def main() -> None:
    settings = get_settings()
    async with async_session_factory() as session:
        result = await session.execute(
            update(Quota).values(
                daily_requests_limit=settings.default_daily_requests,
                monthly_requests_limit=settings.default_monthly_requests,
                daily_tokens_limit=settings.default_daily_tokens,
                monthly_tokens_limit=settings.default_monthly_tokens,
            )
        )
        await session.commit()
        print(f"Updated quotas for {result.rowcount} user(s).")


if __name__ == "__main__":
    asyncio.run(main())
