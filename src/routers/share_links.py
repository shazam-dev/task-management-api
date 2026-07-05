from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.share_link import ShareLinkCreate
from src.services.share_link_service import create_share_link, delete_share_link, get_task_by_share_token

router = APIRouter(prefix="/share-links", tags=["share_links"])


@router.post("/")
async def create_share_link_endpoint(data: ShareLinkCreate, db: AsyncSession = Depends(get_db)):
    return await create_share_link(db, data)


@router.get("/{token}")
async def get_shared_task(token: str, db: AsyncSession = Depends(get_db)):
    return await get_task_by_share_token(db, token)


@router.delete("/{link_id}")
async def delete_share_link_endpoint(link_id: str, db: AsyncSession = Depends(get_db)):
    await delete_share_link(db, link_id)
    return {"message": "Share link deleted successfully"}
