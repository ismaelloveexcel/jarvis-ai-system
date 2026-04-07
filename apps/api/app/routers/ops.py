from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.ops import OpsRequest, OpsResponse, OpsCapabilitiesResponse, RunbookResponse
from app.services.ops_service import OpsService
from app.services.task_service import TaskService
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.guardrails.service import GuardrailService
from app.models.task import TaskStatus

router = APIRouter()


@router.get("/capabilities", response_model=OpsCapabilitiesResponse)
def ops_capabilities():
    service = OpsService()
    return service.capabilities()


@router.get("/status")
def ops_status():
    service = OpsService()
    return service.status()


@router.post("/request", response_model=OpsResponse)
def ops_request(payload: OpsRequest, db: Session = Depends(get_db)):
    if not settings.OPS_ENABLED:
        raise HTTPException(status_code=400, detail="Ops execution is disabled.")

    task_service = TaskService(db)
    approval_service = ApprovalService(db)
    audit_service = AuditService(db)
    guardrail_service = GuardrailService()
    ops_service = OpsService()

    task = task_service.create_task(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        task_type="ops",
        title=payload.title,
    )
    task_service.update_task_status(task, TaskStatus.ANALYZING, current_step="evaluating ops guardrails")

    guardrail = guardrail_service.evaluate_ops(payload.request_type, payload.dict())

    if guardrail["decision"] == "blocked":
        task_service.update_task_status(
            task, TaskStatus.FAILED,
            current_step="blocked",
            result_json={"status": "blocked", "reason": guardrail["reason"]},
        )
        audit_service.log(
            event_type="ops_blocked",
            event_status="blocked",
            details_json={"request_type": payload.request_type, "reason": guardrail["reason"]},
            task_id=task.id,
        )
        return OpsResponse(
            task_id=task.id,
            request_type=payload.request_type,
            execution_mode="blocked",
            result={"status": "blocked", "reason": guardrail["reason"]},
        )

    if guardrail["decision"] == "approval_required":
        task_service.update_task_status(task, TaskStatus.WAITING_FOR_APPROVAL, current_step="waiting for approval")
        context = payload.context.copy()
        if payload.environment:
            context["environment"] = payload.environment
        approval_service.create_approval(
            task_id=task.id,
            action_name=f"ops:{payload.request_type}",
            requested_action={
                "objective": payload.objective,
                "context": context,
                "title": payload.title,
            },
        )
        audit_service.log(
            event_type="ops_approval_requested",
            event_status="pending",
            details_json={"request_type": payload.request_type, "task_id": task.id},
            task_id=task.id,
        )
        return OpsResponse(
            task_id=task.id,
            request_type=payload.request_type,
            execution_mode="pending_approval",
            result={"status": "pending_approval", "reason": guardrail["reason"]},
        )

    # Allowed — execute directly
    task_service.update_task_status(task, TaskStatus.EXECUTING, current_step="executing ops request")
    context = payload.context.copy()
    if payload.environment:
        context["environment"] = payload.environment
    result = ops_service.run(
        request_type=payload.request_type,
        title=payload.title,
        objective=payload.objective,
        context=context,
    )
    task_service.update_task_status(task, TaskStatus.COMPLETED, current_step="completed", result_json=result)
    audit_service.log(
        event_type="ops_completed",
        event_status="completed",
        details_json=result,
        task_id=task.id,
    )
    return OpsResponse(
        task_id=task.id,
        request_type=payload.request_type,
        execution_mode=settings.OPS_MODE,
        result=result,
    )


@router.get("/runbooks", response_model=list[RunbookResponse])
def list_runbooks():
    service = OpsService()
    return service.list_runbooks()


@router.get("/task/{task_id}")
def get_ops_task(task_id: int, db: Session = Depends(get_db)):
    task_service = TaskService(db)
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "title": task.title,
        "status": task.status.value if hasattr(task.status, "value") else task.status,
        "current_step": task.current_step,
        "result": task.result_json,
    }
