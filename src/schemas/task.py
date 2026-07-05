from datetime import datetime

from pydantic import BaseModel

from src.models import Priority


class TaskCreate(BaseModel):
    title: str
    statusId: str
    categoryId: str
    description: str | None = None
    priority: Priority = Priority.MEDIUM
    dueDate: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    statusId: str | None = None
    categoryId: str | None = None
    description: str | None = None
    priority: Priority | None = None
    dueDate: datetime | None = None


class TaskResponse(BaseModel):
    id: str
    userId: str
    title: str
    statusId: str
    categoryId: str
    description: str | None
    priority: Priority
    dueDate: datetime | None
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
