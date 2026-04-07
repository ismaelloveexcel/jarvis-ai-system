from pydantic import BaseModel


class TaskCreateRequest(BaseModel):
    user_id: int = 1
    conversation_id: int | None = None
    task_type: str
    title: str
    context_json: dict = {}


class TaskResponse(BaseModel):
    id: int
    task_type: str
    title: str
    status: str
    current_step: str | None = None
    context_json: dict = {}
    result_json: dict = {}
