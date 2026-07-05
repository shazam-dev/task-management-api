from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Task
from src.schemas.task import TaskCreate, TaskUpdate


async def get_all_tasks(db: AsyncSession, user_id: str | None = None):
    query = select(Task).order_by(Task.createdAt.desc())
    if user_id:
        query = query.where(Task.userId == user_id)
    result = await db.execute(query)
    return result.scalars().all()


async def get_task_by_id(db: AsyncSession, task_id: str):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


async def create_task(db: AsyncSession, user_id: str, data: TaskCreate):
    task = Task(
        userId=user_id,
        title=data.title,
        statusId=data.statusId,
        categoryId=data.categoryId,
        description=data.description,
        priority=data.priority,
        dueDate=data.dueDate,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(db: AsyncSession, task_id: str, user_id: str, data: TaskUpdate):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    if task.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task",
        )
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return task
    for key, value in update_data.items():
        setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: str, user_id: str):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    if task.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task",
        )
    await db.delete(task)
    await db.commit()
