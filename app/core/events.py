import logging
from app.core.database import init_db, async_session_factory
from app.database.models.user import User, UserRole
from app.core.config import get_settings
from app.core.security import hash_password
from sqlalchemy import select
from app.services.lm_studio_service import get_lm_studio_service, close_lm_studio_service
from app.services.model_service import ModelService

logger = logging.getLogger("api")
settings = get_settings()


async def startup_event():
    logger.info("Starting AI API Platform...")
    await init_db()
    logger.info("Database initialized")

    await _create_default_admin()
    await _sync_models()


async def shutdown_event():
    logger.info("Shutting down AI API Platform...")
    await close_lm_studio_service()


async def _create_default_admin():
    async with async_session_factory() as db:
        result = await db.execute(
            select(User).where(User.email == settings.default_admin_email)
        )
        user = result.scalar_one_or_none()
        if not user:
            from app.services.user_service import UserService
            from app.schemas.user import UserCreate
            service = UserService(db)
            await service.create(
                UserCreate(
                    name="Admin",
                    email=settings.default_admin_email,
                    password=settings.default_admin_password,
                    role=UserRole.ADMIN,
                )
            )
            await db.commit()
            logger.info(f"Default admin created: {settings.default_admin_email}")
        else:
            logger.info("Default admin already exists")


async def _sync_models():
    try:
        lm_studio = get_lm_studio_service()
        models = await lm_studio.list_models()
        async with async_session_factory() as db:
            service = ModelService(db)
            await service.sync_from_lm_studio(models)
            await db.commit()
        logger.info(f"Synced {len(models)} models from LM Studio")
    except Exception as e:
        logger.warning(f"Could not sync models from LM Studio: {e}")
