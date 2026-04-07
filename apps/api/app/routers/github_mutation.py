from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.github_mutation import (
    GitHubMutationRequest,
    GitHubMutationResponse,
    GitHubMutationCapabilityResponse,
)
from app.services.task_service import TaskService
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.services.github_mutation_service import GitHubMutationService
from app.guardrails.service import GuardrailService
from app.models.task import TaskStatus

router = APIRouter()


@router.get("/capabilities", response_model=GitHubMutationCapabilityResponse)
def mutation_capabilities():
    caps = GitHubMutationService().capabilities()
    return GitHubMutationCapabilityResponse(**caps)


@router.get("/status/{task_id}")
def mutation_status(task_id: int, db: Session = Depends(get_db)):
    task = TaskService(db).get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task.id,
        "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        "current_step": task.current_step,
        "result_json": task.result_json or {},
    }


@router.post("/", response_model=GitHubMutationResponse)
def run_github_mutation(payload: GitHubMutationRequest, db: Session = Depends(get_db)):
    task_service = TaskService(db)
    approval_service = ApprovalService(db)
    audit_service = AuditService(db)
    guardrail_service = GuardrailService()
    mutation_service = GitHubMutationService()

    repo = payload.repo or settings.GITHUB_DEFAULT_REPO or "unknown/repo"

    task = task_service.create_task(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        task_type="github_mutation",
        title=payload.title,
        context_json={
            "request_type": payload.request_type,
            "repo": repo,
            "objective": payload.objective,
            "context": payload.context,
        },
    )

    audit_service.log(
        event_type="github_mutation_requested",
        event_status="received",
        details_json={
            "request_type": payload.request_type,
            "repo": repo,
            "title": payload.title,
            "objective": payload.objective,
        },
        task_id=task.id,
    )

    guardrail = guardrail_service.evaluate_github_mutation(
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
            event_type="github_merge_blocked",
            event_status="blocked",
            details_json={"reason": guardrail["reason"], "request_type": payload.request_type},
            task_id=task.id,
        )
        return GitHubMutationResponse(
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
            action_name=f"github_mutation:{payload.request_type}",
            requested_action={
                "repo": repo,
                "title": payload.title,
                "objective": payload.objective,
                "context": payload.context,
            },
        )
        audit_service.log(
            event_type="github_mutation_approved",
            event_status="pending",
            details_json={"approval_id": approval.id, "request_type": payload.request_type, "repo": repo},
            task_id=task.id,
        )
        return GitHubMutationResponse(
            task_id=task.id,
            execution_mode="pending_approval",
            result={
                "status": "pending_approval",
                "approval_id": approval.id,
                "reason": guardrail["reason"],
            },
        )

    # Safety model: mutation flows should always require approval in Phase 7
    task_service.update_task_status(
        task,
        TaskStatus.FAILED,
        current_step="blocked",
        result_json={"status": "blocked", "reason": "Mutation path must remain approval-gated in Phase 7."},
    )
    return GitHubMutationResponse(
        task_id=task.id,
        execution_mode="blocked",
        result={"status": "blocked", "reason": "Mutation path must remain approval-gated in Phase 7."},
    )
