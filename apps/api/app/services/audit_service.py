from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(self, event_type: str, event_status: str, details_json: dict, task_id: int | None = None) -> AuditLog:
        record = AuditLog(
            task_id=task_id,
            event_type=event_type,
            event_status=event_status,
            details_json=details_json,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_logs(self) -> list[AuditLog]:
        return self.db.query(AuditLog).order_by(AuditLog.id.desc()).all()
