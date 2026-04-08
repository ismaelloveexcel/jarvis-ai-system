from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.approval import ApprovalDecisionRequest, ApprovalResponse
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.services.task_service import TaskService
from app.services.approval_dispatcher import dispatch_approved_action
from app.models.task import TaskStatus

router = APIRouter()


def _to_response(approval) -> ApprovalResponse:
    return ApprovalResponse(
        id=approval.id,
        task_id=approval.task_id,
        action_name=approval.action_name,
        requested_action=approval.requested_action or {},
        status=approval.status,
        decision_notes=approval.decision_notes,
    )


def _get_pending_approval(approval_service: ApprovalService, approval_id: int):
    approval = approval_service.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval is no longer pending")
    return approval


@router.get("/", response_model=list[ApprovalResponse])
def list_approvals(db: Session = Depends(get_db)):
    approvals = ApprovalService(db).list_approvals()
    return [_to_response(a) for a in approvals]


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve_approval(approval_id: int, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)):
    approval_service = ApprovalService(db)
    audit_service = AuditService(db)
    task_service = TaskService(db)

    approval = _get_pending_approval(approval_service, approval_id)
    approval = approval_service.approve(approval, payload.decision_notes)

    audit_service.log(
        event_type="approval",
        event_status="approved",
        details_json={"approval_id": approval.id, "action_name": approval.action_name},
        task_id=approval.task_id,
    )

    task = task_service.get_task(approval.task_id)
    if task:
        task_service.update_task_status(task, TaskStatus.EXECUTING, current_step="executing after approval")
        result = dispatch_approved_action(approval, task, audit_service)
        task_service.update_task_status(task, TaskStatus.COMPLETED, current_step="completed", result_json=result)

    return _to_response(approval)


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def reject_approval(approval_id: int, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)):
    approval_service = ApprovalService(db)
    audit_service = AuditService(db)
    task_service = TaskService(db)

    approval = _get_pending_approval(approval_service, approval_id)
    approval = approval_service.reject(approval, payload.decision_notes)

    audit_service.log(
        event_type="approval",
        event_status="rejected",
        details_json={"approval_id": approval.id, "action_name": approval.action_name},
        task_id=approval.task_id,
    )

    task = task_service.get_task(approval.task_id)
    if task:
        task_service.update_task_status(
            task,
            TaskStatus.FAILED,
            current_step="rejected",
            result_json={"status": "rejected", "reason": approval.decision_notes or "Approval rejected"},
        )

    return _to_response(approval)
