import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.models.model import Model
from app.schemas.model import ModelCreate, ModelUpdate


class ModelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ModelCreate) -> Model:
        model = Model(**data.model_dump())
        self.db.add(model)
        await self.db.flush()
        return model

    async def get_by_id(self, model_id: uuid.UUID) -> Optional[Model]:
        result = await self.db.execute(select(Model).where(Model.id == model_id))
        return result.scalar_one_or_none()

    async def get_by_model_id(self, model_id: str) -> Optional[Model]:
        result = await self.db.execute(select(Model).where(Model.model_id == model_id))
        return result.scalar_one_or_none()

    async def get_active_models(self) -> list[Model]:
        result = await self.db.execute(
            select(Model).where(Model.is_active == True).order_by(Model.name)
        )
        return list(result.scalars().all())

    async def get_all(self) -> tuple[list[Model], int]:
        count_result = await self.db.execute(select(func.count(Model.id)))
        total = count_result.scalar() or 0
        result = await self.db.execute(select(Model).order_by(Model.name))
        return list(result.scalars().all()), total

    async def update(self, model_id: uuid.UUID, data: ModelUpdate) -> Optional[Model]:
        model = await self.get_by_id(model_id)
        if not model:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(model, key, value)
        await self.db.flush()
        return model

    async def delete(self, model_id: uuid.UUID) -> bool:
        model = await self.get_by_id(model_id)
        if not model:
            return False
        await self.db.delete(model)
        await self.db.flush()
        return True

    async def sync_from_lm_studio(self, lm_studio_models: list[dict]):
        existing = await self.get_active_models()
        existing_ids = {m.model_id for m in existing}

        for lm_model in lm_studio_models:
            model_id = lm_model.get("id")
            if model_id in existing_ids:
                continue
            model = Model(
                model_id=model_id,
                name=lm_model.get("id", model_id),
                provider="lm_studio",
                description=lm_model.get("description"),
            )
            self.db.add(model)

        await self.db.flush()
