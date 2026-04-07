from pydantic import BaseModel
from typing import Any


class ActionRequest(BaseModel):
    user_id: int = 1
    conversation_id: int | None = None
    action_name: str
    payload: dict[str, Any]


class ActionResponse(BaseModel):
    task_id: int | None = None
    action_name: str
    result: dict[str, Any]
