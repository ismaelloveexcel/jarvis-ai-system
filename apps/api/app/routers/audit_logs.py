from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(db: Session = Depends(get_db)):
    logs = AuditService(db).list_logs()
    return [
        AuditLogResponse(
            id=log.id,
            task_id=log.task_id,
            event_type=log.event_type,
            event_status=log.event_status,
            details_json=log.details_json or {},
        )
        for log in logs
    ]
