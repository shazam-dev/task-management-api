from datetime import datetime

from pydantic import BaseModel


class ShareLinkCreate(BaseModel):
    taskId: str
    token: str
    expiresAt: datetime


class ShareLinkResponse(BaseModel):
    id: str
    taskId: str
    token: str
    expiresAt: datetime

    model_config = {"from_attributes": True}
