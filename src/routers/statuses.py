from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.status import StatusCreate
from src.services.status_service import create_status, delete_status, get_all_statuses

router = APIRouter(prefix="/statuses", tags=["statuses"])


@router.get("/")
async def list_statuses(db: AsyncSession = Depends(get_db)):
    return await get_all_statuses(db)


@router.post("/")
async def create_status_endpoint(data: StatusCreate, db: AsyncSession = Depends(get_db)):
    return await create_status(db, data)


@router.delete("/{status_id}")
async def delete_status_endpoint(status_id: str, db: AsyncSession = Depends(get_db)):
    await delete_status(db, status_id)
    return {"message": "Status deleted successfully"}
