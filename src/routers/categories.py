from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.category import CategoryCreate
from src.services.category_service import create_category, delete_category, get_all_categories

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/")
async def list_categories(db: AsyncSession = Depends(get_db)):
    return await get_all_categories(db)


@router.post("/")
async def create_category_endpoint(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    return await create_category(db, data)


@router.delete("/{category_id}")
async def delete_category_endpoint(category_id: str, db: AsyncSession = Depends(get_db)):
    await delete_category(db, category_id)
    return {"message": "Category deleted successfully"}
