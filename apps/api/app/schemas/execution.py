from pydantic import BaseModel, Field
from typing import Any, Literal


class OpenHandsExecutionRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    conversation_id: int | None = None
    request_type: Literal["code_generation", "repo_scaffold", "file_refactor", "bug_fix_plan"]
    title: str = Field(..., min_length=1, max_length=500)
    objective: str = Field(..., min_length=1, max_length=5000)
    context: dict[str, Any] = {}


class OpenHandsExecutionResponse(BaseModel):
    task_id: int
    execution_mode: str
    result: dict[str, Any]


class OpenHandsCapabilityResponse(BaseModel):
    enabled: bool
    mode: str
    base_url: str
    supported_request_types: list[str]
