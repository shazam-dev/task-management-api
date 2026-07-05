from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Category
from src.schemas.category import CategoryCreate


async def get_all_categories(db: AsyncSession):
    result = await db.execute(select(Category).order_by(Category.name))
    return result.scalars().all()


async def create_category(db: AsyncSession, data: CategoryCreate):
    result = await db.execute(select(Category).where(Category.name == data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category already exists",
        )
    category = Category(name=data.name)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def delete_category(db: AsyncSession, category_id: str):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    await db.delete(category)
    await db.commit()
