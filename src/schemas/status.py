from datetime import datetime

from pydantic import BaseModel


class StatusCreate(BaseModel):
    name: str


class StatusResponse(BaseModel):
    id: str
    name: str
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
