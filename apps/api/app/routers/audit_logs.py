import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(event_type: str | None = None, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    try:
        logs = AuditService(db).list_logs(event_type=event_type, limit=limit, offset=offset)
        return [
            AuditLogResponse(
                id=log.id,
                task_id=log.task_id,
                event_type=log.event_type,
                event_status=log.event_status,
                details_json=log.details_json or {},
                created_at=log.created_at,
            )
            for log in logs
        ]
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("list_audit_logs failed")
        raise HTTPException(status_code=500, detail=str(exc))
