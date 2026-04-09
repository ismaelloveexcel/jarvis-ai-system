from pydantic import BaseModel, Field, field_validator
import json


class TaskCreateRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    conversation_id: int | None = None
    task_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=512)
    context_json: dict = {}

    @field_validator('context_json')
    def validate_context_json_size(cls, v):
        """Validate context_json size does not exceed 64KB"""
        if not v:
            return v
        context_json = json.dumps(v)
        if len(context_json.encode('utf-8')) > 65536:  # 64KB
            raise ValueError('context_json size exceeds maximum of 64KB')
        return v


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
