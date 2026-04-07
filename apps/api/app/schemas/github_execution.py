from pydantic import BaseModel
from typing import Any, Literal


class GitHubExecutionRequest(BaseModel):
    user_id: int = 1
    conversation_id: int | None = None
    request_type: Literal["repo_inspect", "branch_plan", "patch_proposal", "pr_draft", "repo_write_request"]
    title: str
    repo: str | None = None
    objective: str
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
