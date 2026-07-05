from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.schemas.auth import LoginRequest, RegisterRequest
from src.utils.security import create_access_token, hash_password, verify_password


async def register_user(db: AsyncSession, data: RegisterRequest):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    hashed_pw = hash_password(data.password)
    user = User(email=data.email, password=hashed_pw, name=data.name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}


async def login_user(db: AsyncSession, data: LoginRequest):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}
