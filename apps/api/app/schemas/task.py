from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    conversation_id: int | None = None
    task_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    context_json: dict = {}


class TaskResponse(BaseModel):
    id: int
    task_type: str
    title: str
    status: str
    current_step: str | None = None
    context_json: dict = {}
    result_json: dict = {}


class TaskStatusResponse(BaseModel):
    task_id: int
    status: str
    current_step: str | None = None
    result_json: dict = {}
