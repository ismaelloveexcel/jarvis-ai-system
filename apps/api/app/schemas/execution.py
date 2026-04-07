from pydantic import BaseModel
from typing import Any, Literal


class OpenHandsExecutionRequest(BaseModel):
    user_id: int = 1
    conversation_id: int | None = None
    request_type: Literal["code_generation", "repo_scaffold", "file_refactor", "bug_fix_plan"]
    title: str
    objective: str
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
