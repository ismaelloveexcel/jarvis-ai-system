from datetime import datetime
from pydantic import BaseModel, field_validator
import json


class ApprovalResponse(BaseModel):
    id: int
    task_id: int
    action_name: str
    requested_action: dict
    status: str
    decision_notes: str | None = None
    expires_at: datetime | None = None
    approved_by: int | None = None
    approved_at: datetime | None = None

    @field_validator('requested_action')
    def validate_requested_action_size(cls, v):
        """Validate requested_action JSON size does not exceed 64KB"""
        if not v:
            return v
        action_json = json.dumps(v)
        if len(action_json.encode('utf-8')) > 65536:  # 64KB
            raise ValueError('requested_action JSON size exceeds maximum of 64KB')
        return v


class ApprovalDecisionRequest(BaseModel):
    decision_notes: str | None = None
