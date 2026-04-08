from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    task_id: int | None = None
    event_type: str
    event_status: str
    details_json: dict
    created_at: datetime | None = None
