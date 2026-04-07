from pydantic import BaseModel


class ApprovalResponse(BaseModel):
    id: int
    task_id: int
    action_name: str
    requested_action: dict
    status: str
    decision_notes: str | None = None


class ApprovalDecisionRequest(BaseModel):
    decision_notes: str | None = None
