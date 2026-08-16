import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_admin_user
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserListResponse
from app.schemas.api_key import APIKeyResponse, APIKeyUpdate, APIKeyListResponse, APIKeyCreatedResponse
from app.schemas.model import ModelCreate, ModelResponse, ModelUpdate, ModelListResponse
from app.schemas.usage import UsageRecordResponse, UsageSummary
from app.schemas.quota import QuotaResponse, QuotaUpdate
from app.services.user_service import UserService
from app.services.api_key_service import APIKeyService
from app.services.model_service import ModelService
from app.services.usage_service import UsageService
from app.services.quota_service import QuotaService
from app.database.models.user import User, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    users, total = await service.get_all(page, size)
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        size=size,
    )


@router.post("/users", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    try:
        user = await service.create(data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UserUpdate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    user = await service.update(uuid.UUID(user_id), data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    deleted = await service.delete(uuid.UUID(user_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "User deleted"}


@router.get("/users/{user_id}/api-keys", response_model=APIKeyListResponse)
async def list_user_api_keys(
    user_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = APIKeyService(db)
    keys, total = await service.get_user_keys(uuid.UUID(user_id), page, size)
    return APIKeyListResponse(
        items=[APIKeyResponse.model_validate(k) for k in keys],
        total=total,
        page=page,
        size=size,
    )


@router.put("/api-keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    data: APIKeyUpdate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = APIKeyService(db)
    updated = await service.update(uuid.UUID(key_id), data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return APIKeyResponse.model_validate(updated)


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = APIKeyService(db)
    deleted = await service.delete(uuid.UUID(key_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return {"message": "API key deleted"}


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = ModelService(db)
    models, total = await service.get_all()
    return ModelListResponse(
        items=[ModelResponse.model_validate(m) for m in models],
        total=total,
    )


@router.post("/models", response_model=ModelResponse)
async def create_model(
    data: ModelCreate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = ModelService(db)
    model = await service.create(data)
    return ModelResponse.model_validate(model)


@router.put("/models/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    data: ModelUpdate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = ModelService(db)
    model = await service.update(uuid.UUID(model_id), data)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return ModelResponse.model_validate(model)


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = ModelService(db)
    deleted = await service.delete(uuid.UUID(model_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return {"message": "Model deleted"}


@router.get("/users/{user_id}/usage", response_model=UsageSummary)
async def get_user_usage_summary(
    user_id: str,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = UsageService(db)
    return await service.get_user_summary(uuid.UUID(user_id))


@router.get("/users/{user_id}/quota", response_model=QuotaResponse)
async def get_user_quota(
    user_id: str,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = QuotaService(db)
    quota = await service.get_quota(uuid.UUID(user_id))
    if not quota:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quota not found")
    return QuotaResponse.model_validate(quota)


@router.put("/users/{user_id}/quota", response_model=QuotaResponse)
async def update_user_quota(
    user_id: str,
    data: QuotaUpdate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = QuotaService(db)
    quota = await service.update_quota(uuid.UUID(user_id), **data.model_dump(exclude_unset=True))
    if not quota:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quota not found")
    return QuotaResponse.model_validate(quota)
