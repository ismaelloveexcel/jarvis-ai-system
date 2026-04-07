from pydantic import BaseModel
from typing import Optional


class OpsRequest(BaseModel):
    user_id: int
    conversation_id: Optional[int] = None
    request_type: str  # deployment_request | promote_environment | rollback_request | maintenance_check | runbook_lookup
    title: str
    objective: str
    environment: Optional[str] = None
    context: dict = {}


class OpsResponse(BaseModel):
    task_id: Optional[int] = None
    request_type: str
    execution_mode: str
    result: dict


class OpsCapabilitiesResponse(BaseModel):
    enabled: bool
    mode: str
    default_environment: str
    allow_live_maintenance: bool
    supported_types: list[str]


class RunbookResponse(BaseModel):
    runbook_id: str
    title: str
    description: str
    steps: list[str]
