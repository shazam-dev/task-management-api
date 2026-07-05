from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Status
from src.schemas.status import StatusCreate


async def get_all_statuses(db: AsyncSession):
    result = await db.execute(select(Status).order_by(Status.name))
    return result.scalars().all()


async def create_status(db: AsyncSession, data: StatusCreate):
    result = await db.execute(select(Status).where(Status.name == data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Status already exists",
        )
    st = Status(name=data.name)
    db.add(st)
    await db.commit()
    await db.refresh(st)
    return st


async def delete_status(db: AsyncSession, status_id: str):
    result = await db.execute(select(Status).where(Status.id == status_id))
    st = result.scalar_one_or_none()
    if not st:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Status not found",
        )
    await db.delete(st)
    await db.commit()
