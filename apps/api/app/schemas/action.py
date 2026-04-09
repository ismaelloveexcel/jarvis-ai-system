from pydantic import BaseModel, Field
from typing import Any


class ActionRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    conversation_id: int | None = None
    action_name: str = Field(..., min_length=1, max_length=255)
    payload: dict[str, Any]


class ActionResponse(BaseModel):
    task_id: int | None = None
    action_name: str
    result: dict[str, Any]
