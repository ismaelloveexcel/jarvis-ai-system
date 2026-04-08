import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db, get_background_db
from app.schemas.execution import (
    OpenHandsExecutionRequest,
    OpenHandsExecutionResponse,
    OpenHandsCapabilityResponse,
)
from app.services.task_service import TaskService
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.services.openhands_service import OpenHandsService
from app.guardrails.service import GuardrailService
from app.models.task import TaskStatus

router = APIRouter()
logger = logging.getLogger(__name__)


def _execute_openhands_background(task_id: int, request_type: str, title: str, objective: str, context: dict):
    db = get_background_db()
    try:
        task_service = TaskService(db)
        audit_service = AuditService(db)
        openhands_service = OpenHandsService()

        task = task_service.get_task(task_id)
        if not task:
            logger.error("Background openhands execution: task %s not found", task_id)
            return
        task_service.update_task_status(task, TaskStatus.ANALYZING, current_step="analyzing execution")
        task_service.update_task_status(task, TaskStatus.PLANNING, current_step="planning execution")
        task_service.update_task_status(task, TaskStatus.EXECUTING, current_step="executing with OpenHands")

        audit_service.log(
            event_type="openhands_requested",
            event_status="started",
            details_json={"request_type": request_type, "title": title},
            task_id=task.id,
        )

        result = openhands_service.run(
            request_type=request_type,
            title=title,
            objective=objective,
            context=context,
        )

        task_service.update_task_status(task, TaskStatus.COMPLETED, current_step="completed", result_json=result)
        audit_service.log(
            event_type="openhands_completed", event_status="completed",
            details_json=result, task_id=task.id,
        )
    except Exception as exc:
        logger.exception("Background openhands execution failed for task %s", task_id)
        task_service = TaskService(db)
        audit_service = AuditService(db)
        task = task_service.get_task(task_id)
        if task:
            task_service.update_task_status(task, TaskStatus.FAILED, current_step="failed", result_json={"error": str(exc)})
            audit_service.log(
                event_type="openhands_failed", event_status="failed",
                details_json={"error": str(exc)}, task_id=task.id,
            )
    finally:
        db.close()


@router.get("/capabilities", response_model=OpenHandsCapabilityResponse)
def execution_capabilities():
    caps = OpenHandsService().capabilities()
    return OpenHandsCapabilityResponse(**caps)


@router.get("/status/{task_id}")
def execution_status(task_id: int, db: Session = Depends(get_db)):
    task = TaskService(db).get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task.id,
        "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        "current_step": task.current_step,
        "result_json": task.result_json or {},
    }


@router.post("/openhands", response_model=OpenHandsExecutionResponse, status_code=202)
def run_openhands(payload: OpenHandsExecutionRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task_service = TaskService(db)
    approval_service = ApprovalService(db)
    audit_service = AuditService(db)
    guardrail_service = GuardrailService()
    openhands_service = OpenHandsService()

    task = task_service.create_task(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        task_type="execution",
        title=payload.title,
        context_json={
            "request_type": payload.request_type,
            "objective": payload.objective,
            "context": payload.context,
        },
    )

    audit_service.log(
        event_type="execution_requested",
        event_status="received",
        details_json={
            "request_type": payload.request_type,
            "title": payload.title,
            "objective": payload.objective,
        },
        task_id=task.id,
    )

    guardrail = guardrail_service.evaluate_execution(
        request_type=payload.request_type,
        payload={
            "title": payload.title,
            "objective": payload.objective,
            "context": payload.context,
        },
    )

    if guardrail["decision"] == "blocked":
        task_service.update_task_status(
            task,
            TaskStatus.FAILED,
            current_step="blocked",
            result_json={"status": "blocked", "reason": guardrail["reason"]},
        )
        audit_service.log(
            event_type="execution_blocked",
            event_status="blocked",
            details_json={"reason": guardrail["reason"], "request_type": payload.request_type},
            task_id=task.id,
        )
        return OpenHandsExecutionResponse(
            task_id=task.id,
            execution_mode="blocked",
            result={"status": "blocked", "reason": guardrail["reason"]},
        )

    if guardrail["decision"] == "approval_required":
        task_service.update_task_status(
            task,
            TaskStatus.WAITING_FOR_APPROVAL,
            current_step="waiting_for_approval",
        )
        approval = approval_service.create_approval(
            task_id=task.id,
            action_name=f"execution:{payload.request_type}",
            requested_action={
                "title": payload.title,
                "objective": payload.objective,
                "context": payload.context,
            },
        )
        audit_service.log(
            event_type="approval_requested",
            event_status="pending",
            details_json={
                "approval_id": approval.id,
                "request_type": payload.request_type,
            },
            task_id=task.id,
        )
        return OpenHandsExecutionResponse(
            task_id=task.id,
            execution_mode="pending_approval",
            result={
                "status": "pending_approval",
                "approval_id": approval.id,
                "reason": guardrail["reason"],
            },
        )

    task_service.update_task_status(task, TaskStatus.ANALYZING, current_step="queued for execution")

    background_tasks.add_task(
        _execute_openhands_background,
        task_id=task.id,
        request_type=payload.request_type,
        title=payload.title,
        objective=payload.objective,
        context=payload.context,
    )

    return OpenHandsExecutionResponse(
        task_id=task.id,
        execution_mode="async",
        result={"status": "accepted", "message": "Task queued for background execution"},
    )
