from pydantic import BaseModel, Field, field_validator
from typing import Any, Literal
import json


class GitHubMutationRequest(BaseModel):
    user_id: int = 1
    conversation_id: int | None = None
    request_type: Literal["create_branch", "create_patch_artifact", "create_pr_draft", "execute_repo_write", "merge_request"]
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


class GitHubMutationResponse(BaseModel):
    task_id: int
    execution_mode: str
    result: dict[str, Any]


class GitHubMutationCapabilityResponse(BaseModel):
    enabled: bool
    mode: str
    default_base_branch: str
    default_draft_pr: bool
    supported_request_types: list[str]
