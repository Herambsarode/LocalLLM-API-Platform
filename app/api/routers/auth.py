import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.user import UserCreate, UserResponse, LoginRequest, TokenResponse
from app.schemas.api_key import APIKeyCreate, APIKeyCreatedResponse, APIKeyResponse, APIKeyListResponse, APIKeyUpdate
from app.services.auth_service import AuthService
from app.services.api_key_service import APIKeyService
from app.database.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        user = await auth_service.register(data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        token = await auth_service.login(data)
        return TokenResponse(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/api-keys", response_model=APIKeyCreatedResponse)
async def create_api_key(
    data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = APIKeyService(db)
    key_obj, raw_key = await service.create(current_user.id, data)
    resp = APIKeyResponse.model_validate(key_obj)
    return APIKeyCreatedResponse(**resp.model_dump(), raw_key=raw_key)


@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = APIKeyService(db)
    keys, total = await service.get_user_keys(current_user.id, page, size)
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = APIKeyService(db)
    key_obj = await service.get_by_id(uuid.UUID(key_id))
    if not key_obj or key_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    updated = await service.update(uuid.UUID(key_id), data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return APIKeyResponse.model_validate(updated)


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = APIKeyService(db)
    key_obj = await service.get_by_id(uuid.UUID(key_id))
    if not key_obj or key_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    await service.delete(uuid.UUID(key_id))
    return {"message": "API key deleted"}


@router.post("/api-keys/{key_id}/rotate", response_model=APIKeyCreatedResponse)
async def rotate_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = APIKeyService(db)
    key_obj = await service.get_by_id(uuid.UUID(key_id))
    if not key_obj or key_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    updated, raw_key = await service.rotate(uuid.UUID(key_id))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    resp = APIKeyResponse.model_validate(updated)
    return APIKeyCreatedResponse(**resp.model_dump(), raw_key=raw_key)
