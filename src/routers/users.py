from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import User
from src.schemas.user import UserResponse, UserUpdate
from src.services.user_service import delete_user, get_all_users, get_user_by_id, update_user
from src.utils.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
async def list_users(db: AsyncSession = Depends(get_db)):
    users = await get_all_users(db)
    return [UserResponse.model_validate(u) for u in users]


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_id(db, user_id)
    return UserResponse.model_validate(user)


@router.put("/{user_id}")
async def update_user_endpoint(
    user_id: str,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_user(db, user_id, data)


@router.delete("/{user_id}")
async def delete_user_endpoint(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_user(db, user_id)
    return {"message": "User deleted successfully"}
