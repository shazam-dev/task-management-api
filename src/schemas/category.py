from datetime import datetime

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str


class CategoryResponse(BaseModel):
    id: str
    name: str
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
