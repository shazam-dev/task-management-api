from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import User
from src.schemas.task import TaskCreate, TaskUpdate
from src.services.task_service import create_task, delete_task, get_all_tasks, get_task_by_id, update_task
from src.utils.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/")
async def list_tasks(
    user_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_tasks(db, user_id)


@router.get("/{task_id}")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    return await get_task_by_id(db, task_id)


@router.post("/")
async def create_task_endpoint(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_task(db, current_user.id, data)


@router.put("/{task_id}")
async def update_task_endpoint(
    task_id: str,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_task(db, task_id, current_user.id, data)


@router.delete("/{task_id}")
async def delete_task_endpoint(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_task(db, task_id, current_user.id)
    return {"message": "Task deleted successfully"}
