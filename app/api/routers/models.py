import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.model_service import ModelService
from app.services.lm_studio_service import get_lm_studio_service

logger = logging.getLogger("api")
router = APIRouter(tags=["models"])


@router.get("/v1/models")
async def list_models(db: AsyncSession = Depends(get_db)):
    lm_studio = get_lm_studio_service()
    try:
        lm_models = await lm_studio.list_models()
    except Exception as e:
        logger.warning(f"Could not fetch models from LM Studio: {e}")
        lm_models = []

    model_service = ModelService(db)
    db_models, _ = await model_service.get_all()

    seen_ids = set()
    data = []

    for m in lm_models:
        mid = m.get("id")
        if mid and mid not in seen_ids:
            seen_ids.add(mid)
            data.append({
                "id": mid,
                "object": "model",
                "created": m.get("created", 0),
                "owned_by": m.get("owned_by", "lm_studio"),
                "permission": [],
                "root": mid,
                "parent": None,
            })

    for m in db_models:
        if m.model_id not in seen_ids:
            seen_ids.add(m.model_id)
            data.append({
                "id": m.model_id,
                "object": "model",
                "created": int(m.created_at.timestamp()),
                "owned_by": m.provider,
                "permission": [],
                "root": m.model_id,
                "parent": None,
            })

    return {
        "object": "list",
        "data": data,
    }


@router.get("/v1/models/{model_id}")
async def retrieve_model(model_id: str, db: AsyncSession = Depends(get_db)):
    model_service = ModelService(db)
    model = await model_service.get_by_model_id(model_id)
    if model:
        return {
            "id": model.model_id,
            "object": "model",
            "created": int(model.created_at.timestamp()),
            "owned_by": model.provider,
            "permission": [],
            "root": model.model_id,
            "parent": None,
        }

    lm_studio = get_lm_studio_service()
    lm_models = await lm_studio.list_models()
    for m in lm_models:
        if m.get("id") == model_id:
            return {
                "id": m["id"],
                "object": "model",
                "created": m.get("created", 0),
                "owned_by": m.get("owned_by", "lm_studio"),
                "permission": [],
                "root": m["id"],
                "parent": None,
            }

    from fastapi import HTTPException, status
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
