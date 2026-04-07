from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.action import ActionRequest, ActionResponse
from app.services.action_service import ActionService
from app.services.task_service import TaskService
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.guardrails.service import GuardrailService
from app.models.task import TaskStatus

router = APIRouter()


@router.get("/available")
def list_available_actions():
    return ActionService().list_actions()


@router.post("/", response_model=ActionResponse)
def run_action(payload: ActionRequest, db: Session = Depends(get_db)):
    task_service = TaskService(db)
    action_service = ActionService()
    approval_service = ApprovalService(db)
    audit_service = AuditService(db)
    guardrail_service = GuardrailService()

    task = task_service.create_task(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        task_type="action",
        title=f"Action: {payload.action_name}",
        context_json={"action_name": payload.action_name, "payload": payload.payload},
    )

    audit_service.log(
        event_type="action_requested",
        event_status="received",
        details_json={"action_name": payload.action_name, "payload": payload.payload},
        task_id=task.id,
    )

    try:
        # Phase 3: Guardrail evaluation
        task_service.update_task_status(task, TaskStatus.ANALYZING, current_step="guardrail evaluation")
        guardrail = guardrail_service.evaluate(payload.action_name, payload.payload)

        # BLOCKED
        if guardrail["decision"] == "blocked":
            task_service.update_task_status(
                task, TaskStatus.FAILED, current_step="blocked",
                result_json={"status": "blocked", "reason": guardrail["reason"]},
            )
            audit_service.log(
                event_type="action_blocked", event_status="blocked",
                details_json={"action_name": payload.action_name, "reason": guardrail["reason"]},
                task_id=task.id,
            )
            return ActionResponse(task_id=task.id, action_name=payload.action_name,
                                  result={"status": "blocked", "reason": guardrail["reason"]})

        # APPROVAL REQUIRED
        if guardrail["decision"] == "approval_required":
            task_service.update_task_status(task, TaskStatus.WAITING_FOR_APPROVAL, current_step="waiting_for_approval")
            approval = approval_service.create_approval(
                task_id=task.id, action_name=payload.action_name, requested_action=payload.payload,
            )
            audit_service.log(
                event_type="approval_requested", event_status="pending",
                details_json={"approval_id": approval.id, "action_name": payload.action_name},
                task_id=task.id,
            )
            return ActionResponse(task_id=task.id, action_name=payload.action_name,
                                  result={"status": "pending_approval", "approval_id": approval.id, "reason": guardrail["reason"]})

        # ALLOWED - resolve execution mode and run
        task_service.update_task_status(task, TaskStatus.PLANNING, current_step="resolving execution mode")

        mode = action_service.resolve_execution_mode(payload.action_name)
        audit_service.log(
            event_type="mcp_requested" if mode == "mcp" else "action_requested",
            event_status="routing",
            details_json={"action_name": payload.action_name, "execution_mode": mode},
            task_id=task.id,
        )

        task_service.update_task_status(task, TaskStatus.EXECUTING, current_step=f"executing ({mode})")

        result = action_service.run_action(action_name=payload.action_name, payload=payload.payload)

        task_service.update_task_status(task, TaskStatus.COMPLETED, current_step="completed", result_json=result)

        audit_event = "mcp_completed" if result.get("execution_mode") == "mcp" else "action_execution"
        audit_service.log(
            event_type=audit_event, event_status="completed",
            details_json=result, task_id=task.id,
        )

        return ActionResponse(task_id=task.id, action_name=payload.action_name, result=result)

    except Exception as exc:
        task_service.update_task_status(
            task, TaskStatus.FAILED, current_step="failed", result_json={"error": str(exc)},
        )
        audit_service.log(
            event_type="mcp_failed", event_status="failed",
            details_json={"action_name": payload.action_name, "error": str(exc)},
            task_id=task.id,
        )
        return ActionResponse(task_id=task.id, action_name=payload.action_name,
                              result={"status": "failed", "error": str(exc)})
