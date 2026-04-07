from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.approval import ApprovalDecisionRequest, ApprovalResponse
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.services.task_service import TaskService
from app.services.action_service import ActionService
from app.services.openhands_service import OpenHandsService
from app.services.github_execution_service import GitHubExecutionService
from app.services.github_mutation_service import GitHubMutationService
from app.models.task import TaskStatus

router = APIRouter()


@router.get("/", response_model=list[ApprovalResponse])
def list_approvals(db: Session = Depends(get_db)):
    approvals = ApprovalService(db).list_approvals()
    return [
        ApprovalResponse(
            id=a.id,
            task_id=a.task_id,
            action_name=a.action_name,
            requested_action=a.requested_action or {},
            status=a.status,
            decision_notes=a.decision_notes,
        )
        for a in approvals
    ]


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve_approval(approval_id: int, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)):
    approval_service = ApprovalService(db)
    audit_service = AuditService(db)
    task_service = TaskService(db)
    action_service = ActionService()
    openhands_service = OpenHandsService()
    github_service = GitHubExecutionService()
    github_mutation_service = GitHubMutationService()

    approval = approval_service.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval is no longer pending")

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

        if approval.action_name.startswith("execution:"):
            request_type = approval.action_name.split("execution:", 1)[1]
            result = openhands_service.run(
                request_type=request_type,
                title=task.title,
                objective=approval.requested_action.get("objective", ""),
                context=approval.requested_action.get("context", {}),
            )
            task_service.update_task_status(task, TaskStatus.COMPLETED, current_step="completed", result_json=result)
            audit_service.log(
                event_type="openhands_completed",
                event_status="completed",
                details_json=result,
                task_id=task.id,
            )

        elif approval.action_name.startswith("github_mutation:"):
            request_type = approval.action_name.split("github_mutation:", 1)[1]
            repo = approval.requested_action.get("repo", "unknown/repo")
            result = github_mutation_service.run(
                request_type=request_type,
                repo=repo,
                title=approval.requested_action.get("title", task.title),
                objective=approval.requested_action.get("objective", ""),
                context=approval.requested_action.get("context", {}),
            )
            task_service.update_task_status(task, TaskStatus.COMPLETED, current_step="completed", result_json=result)

            if request_type == "create_branch":
                audit_service.log(
                    event_type="github_branch_created",
                    event_status="completed",
                    details_json=result,
                    task_id=task.id,
                )
            elif request_type == "create_patch_artifact":
                audit_service.log(
                    event_type="github_patch_artifact_created",
                    event_status="completed",
                    details_json=result,
                    task_id=task.id,
                )
            elif request_type == "create_pr_draft":
                audit_service.log(
                    event_type="github_pr_created",
                    event_status="completed",
                    details_json=result,
                    task_id=task.id,
                )
            else:
                audit_service.log(
                    event_type="github_mutation_approved",
                    event_status="completed",
                    details_json=result,
                    task_id=task.id,
                )

        elif approval.action_name.startswith("github:"):
            request_type = approval.action_name.split("github:", 1)[1]
            repo = approval.requested_action.get("repo", "unknown/repo")
            result = github_service.run(
                request_type=request_type,
                repo=repo,
                title=approval.requested_action.get("title", task.title),
                objective=approval.requested_action.get("objective", ""),
                context=approval.requested_action.get("context", {}),
            )
            task_service.update_task_status(task, TaskStatus.COMPLETED, current_step="completed", result_json=result)
            audit_service.log(
                event_type="github_completed",
                event_status="completed",
                details_json=result,
                task_id=task.id,
            )

        else:
            result = action_service.run_action(
                action_name=approval.action_name,
                payload=approval.requested_action,
            )
            task_service.update_task_status(task, TaskStatus.COMPLETED, current_step="completed", result_json=result)
            audit_service.log(
                event_type="action_execution",
                event_status="completed",
                details_json=result,
                task_id=task.id,
            )

    return ApprovalResponse(
        id=approval.id,
        task_id=approval.task_id,
        action_name=approval.action_name,
        requested_action=approval.requested_action or {},
        status=approval.status,
        decision_notes=approval.decision_notes,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def reject_approval(approval_id: int, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)):
    approval_service = ApprovalService(db)
    audit_service = AuditService(db)
    task_service = TaskService(db)

    approval = approval_service.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval is no longer pending")

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

    return ApprovalResponse(
        id=approval.id,
        task_id=approval.task_id,
        action_name=approval.action_name,
        requested_action=approval.requested_action or {},
        status=approval.status,
        decision_notes=approval.decision_notes,
    )
