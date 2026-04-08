from datetime import datetime

from pydantic import BaseModel


class ApprovalResponse(BaseModel):
    id: int
    task_id: int
    action_name: str
    requested_action: dict
    status: str
    decision_notes: str | None = None
    expires_at: datetime | None = None


class ApprovalDecisionRequest(BaseModel):
    decision_notes: str | None = None
