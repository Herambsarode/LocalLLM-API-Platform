import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.models.user import User, UserRole
from app.database.models.quota import Quota
from app.database.models.billing import BillingAccount
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: UserCreate) -> User:
        user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
        )
        self.db.add(user)
        await self.db.flush()

        quota = Quota(user_id=user.id)
        self.db.add(quota)

        billing = BillingAccount(user_id=user.id)
        self.db.add(billing)

        await self.db.flush()
        return user

    async def get_by_id(self, user_id: str | uuid.UUID) -> Optional[User]:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all(self, page: int = 1, size: int = 20) -> tuple[list[User], int]:
        offset = (page - 1) * size
        count_result = await self.db.execute(select(func.count(User.id)))
        total = count_result.scalar() or 0
        result = await self.db.execute(
            select(User).offset(offset).limit(size).order_by(User.created_at.desc())
        )
        return list(result.scalars().all()), total

    async def update(self, user_id: uuid.UUID, data: UserUpdate) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))
        for key, value in update_data.items():
            setattr(user, key, value)
        await self.db.flush()
        return user

    async def delete(self, user_id: uuid.UUID) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        await self.db.delete(user)
        await self.db.flush()
        return True
