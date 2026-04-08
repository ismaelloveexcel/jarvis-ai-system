import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db, get_background_db
from app.schemas.github_execution import (
    GitHubExecutionRequest,
    GitHubExecutionResponse,
    GitHubCapabilityResponse,
)
from app.services.task_service import TaskService
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.services.github_execution_service import GitHubExecutionService
from app.guardrails.service import GuardrailService
from app.models.task import TaskStatus

router = APIRouter()
logger = logging.getLogger(__name__)


def _execute_github_background(task_id: int, request_type: str, repo: str, title: str, objective: str, context: dict):
    db = get_background_db()
    try:
        task_service = TaskService(db)
        audit_service = AuditService(db)
        github_service = GitHubExecutionService()

        task = task_service.get_task(task_id)
        task_service.update_task_status(task, TaskStatus.ANALYZING, current_step="analyzing github request")
        task_service.update_task_status(task, TaskStatus.PLANNING, current_step="planning github workflow")
        task_service.update_task_status(task, TaskStatus.EXECUTING, current_step="executing github workflow")

        result = github_service.run(
            request_type=request_type, repo=repo, title=title, objective=objective, context=context,
        )

        task_service.update_task_status(task, TaskStatus.COMPLETED, current_step="completed", result_json=result)
        audit_service.log(
            event_type="github_completed", event_status="completed",
            details_json=result, task_id=task.id,
        )
    except Exception as exc:
        logger.exception("Background github execution failed for task %s", task_id)
        task_service = TaskService(db)
        audit_service = AuditService(db)
        task = task_service.get_task(task_id)
        if task:
            task_service.update_task_status(task, TaskStatus.FAILED, current_step="failed", result_json={"error": str(exc)})
            audit_service.log(
                event_type="github_failed", event_status="failed",
                details_json={"error": str(exc)}, task_id=task.id,
            )
    finally:
        db.close()


@router.get("/capabilities", response_model=GitHubCapabilityResponse)
def github_capabilities():
    caps = GitHubExecutionService().capabilities()
    return GitHubCapabilityResponse(**caps)


@router.get("/status/{task_id}")
def github_status(task_id: int, db: Session = Depends(get_db)):
    task = TaskService(db).get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task.id,
        "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        "current_step": task.current_step,
        "result_json": task.result_json or {},
    }


@router.post("/", response_model=GitHubExecutionResponse, status_code=202)
def run_github_execution(payload: GitHubExecutionRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task_service = TaskService(db)
    approval_service = ApprovalService(db)
    audit_service = AuditService(db)
    guardrail_service = GuardrailService()
    github_service = GitHubExecutionService()

    repo = payload.repo or settings.GITHUB_DEFAULT_REPO or "unknown/repo"

    task = task_service.create_task(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        task_type="github_execution",
        title=payload.title,
        context_json={
            "request_type": payload.request_type,
            "repo": repo,
            "objective": payload.objective,
            "context": payload.context,
        },
    )

    audit_service.log(
        event_type="github_requested",
        event_status="received",
        details_json={
            "request_type": payload.request_type,
            "repo": repo,
            "title": payload.title,
            "objective": payload.objective,
        },
        task_id=task.id,
    )

    guardrail = guardrail_service.evaluate_github_execution(
        request_type=payload.request_type,
        payload={
            "repo": repo,
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
            event_type="github_write_blocked",
            event_status="blocked",
            details_json={"reason": guardrail["reason"], "request_type": payload.request_type},
            task_id=task.id,
        )
        return GitHubExecutionResponse(
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
            action_name=f"github:{payload.request_type}",
            requested_action={
                "repo": repo,
                "title": payload.title,
                "objective": payload.objective,
                "context": payload.context,
            },
        )
        audit_service.log(
            event_type="github_approval_requested",
            event_status="pending",
            details_json={"approval_id": approval.id, "request_type": payload.request_type, "repo": repo},
            task_id=task.id,
        )
        return GitHubExecutionResponse(
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
        _execute_github_background,
        task_id=task.id,
        request_type=payload.request_type,
        repo=repo,
        title=payload.title,
        objective=payload.objective,
        context=payload.context,
    )

    return GitHubExecutionResponse(
        task_id=task.id,
        execution_mode="async",
        result={"status": "accepted", "message": "Task queued for background execution"},
    )
