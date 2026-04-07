from pydantic import BaseModel
from typing import Any, Literal


class GitHubMutationRequest(BaseModel):
    user_id: int = 1
    conversation_id: int | None = None
    request_type: Literal["create_branch", "create_patch_artifact", "create_pr_draft", "execute_repo_write", "merge_request"]
    title: str
    repo: str | None = None
    objective: str
    context: dict[str, Any] = {}


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
