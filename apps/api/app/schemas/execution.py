from pydantic import BaseModel, Field, field_validator
from typing import Any, Literal
import json


class OpenHandsExecutionRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    conversation_id: int | None = None
    request_type: Literal["code_generation", "repo_scaffold", "file_refactor", "bug_fix_plan"]
    title: str = Field(..., min_length=1, max_length=512)
    objective: str = Field(..., min_length=1, max_length=2048)
    context: dict[str, Any] = {}

    @field_validator('context')
    def validate_context_size(cls, v):
        """Validate context JSON size does not exceed 64KB"""
        if not v:
            return v
        context_json = json.dumps(v)
        if len(context_json.encode('utf-8')) > 65536:  # 64KB
            raise ValueError('context JSON size exceeds maximum of 64KB')
        return v


class OpenHandsExecutionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    task_id: int
    execution_mode: str
    result: dict[str, Any]


class OpenHandsCapabilityResponse(BaseModel):
    enabled: bool
    mode: str
    base_url: str
    supported_request_types: list[str]
