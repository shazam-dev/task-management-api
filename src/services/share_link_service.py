from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ShareLink, Task
from src.schemas.share_link import ShareLinkCreate


async def create_share_link(db: AsyncSession, data: ShareLinkCreate):
    result = await db.execute(select(Task).where(Task.id == data.taskId))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    result = await db.execute(select(ShareLink).where(ShareLink.token == data.token))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Token already exists",
        )
    link = ShareLink(taskId=data.taskId, token=data.token, expiresAt=data.expiresAt)
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


async def get_task_by_share_token(db: AsyncSession, token: str):
    result = await db.execute(select(ShareLink).where(ShareLink.token == token))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found",
        )
    if link.expiresAt < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired",
        )
    result = await db.execute(select(Task).where(Task.id == link.taskId))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


async def delete_share_link(db: AsyncSession, link_id: str):
    result = await db.execute(select(ShareLink).where(ShareLink.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found",
        )
    await db.delete(link)
    await db.commit()
