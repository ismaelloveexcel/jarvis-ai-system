from pydantic import BaseModel, Field
from typing import Any, Literal


class OpsRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    conversation_id: int | None = None
    request_type: Literal["deployment_request", "promote_environment", "rollback_request", "maintenance_check", "runbook_lookup"]
    title: str = Field(..., min_length=1, max_length=500)
    environment: Literal["dev", "staging", "production"] = "dev"
    context: dict[str, Any] = {}


class OpsResponse(BaseModel):
    task_id: int
    execution_mode: str
    result: dict[str, Any]


class OpsCapabilitiesResponse(BaseModel):
    enabled: bool
    mode: str
    default_environment: str
    supported_request_types: list[str]


class RunbookResponse(BaseModel):
    name: str
    path: str
