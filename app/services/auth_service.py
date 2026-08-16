from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models.user import User, UserRole
from app.schemas.user import UserCreate, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.services.user_service import UserService


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def register(self, data: UserCreate) -> User:
        existing = await self.user_service.get_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")
        return await self.user_service.create(data)

    async def login(self, data: LoginRequest) -> str:
        user = await self.user_service.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is disabled")
        return create_access_token({"sub": str(user.id), "role": user.role.value})

    async def get_current_user(self, token: str) -> User:
        payload = decode_access_token(token)
        if not payload:
            raise ValueError("Invalid or expired token")
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
        user = await self.user_service.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        return user

    async def verify_admin(self, token: str) -> User:
        user = await self.get_current_user(token)
        if user.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        return user
