from pydantic import BaseModel, Field
from typing import Any, Literal


class GitHubExecutionRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    conversation_id: int | None = None
    request_type: Literal["repo_inspect", "branch_plan", "patch_proposal", "pr_draft", "repo_write_request"]
    title: str = Field(..., min_length=1, max_length=500)
    repo: str | None = None
    objective: str = Field(..., min_length=1, max_length=5000)
    context: dict[str, Any] = {}


class GitHubExecutionResponse(BaseModel):
    task_id: int
    execution_mode: str
    result: dict[str, Any]


class GitHubCapabilityResponse(BaseModel):
    enabled: bool
    mode: str
    default_repo: str
    supported_request_types: list[str]
