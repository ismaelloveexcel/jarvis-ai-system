from pydantic import BaseModel, Field, field_validator
from typing import Any, Literal
import json


class GitHubExecutionRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    conversation_id: int | None = None
    request_type: Literal["repo_inspect", "branch_plan", "patch_proposal", "pr_draft", "repo_write_request"]
    title: str = Field(..., min_length=1, max_length=512)
    repo: str | None = None
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


class GitHubExecutionResponse(BaseModel):
    task_id: int
    execution_mode: str
    result: dict[str, Any]


class GitHubCapabilityResponse(BaseModel):
    enabled: bool
    mode: str
    default_repo: str
    supported_request_types: list[str]
