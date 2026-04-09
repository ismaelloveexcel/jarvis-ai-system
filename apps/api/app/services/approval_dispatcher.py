from app.services.openhands_service import OpenHandsService
from app.services.github_execution_service import GitHubExecutionService
from app.services.github_mutation_service import GitHubMutationService
from app.services.ops_service import OpsService
from app.services.action_service import ActionService
from app.services.audit_service import AuditService


def _dispatch_ops(approval, task, audit_service: AuditService) -> dict:
    ops_service = OpsService()
    request_type = approval.action_name.split("ops:", 1)[1]
    result = ops_service.run(
        request_type=request_type,
        title=approval.requested_action.get("title", task.title),
        environment=approval.requested_action.get("environment", "dev"),
        context=approval.requested_action.get("context", {}),
    )
    audit_service.log(
        event_type="ops_completed",
        event_status="completed",
        details_json=result,
        task_id=task.id,
    )
    return result


def _dispatch_execution(approval, task, audit_service: AuditService) -> dict:
    openhands_service = OpenHandsService()
    request_type = approval.action_name.split("execution:", 1)[1]
    result = openhands_service.run(
        request_type=request_type,
        title=task.title,
        objective=approval.requested_action.get("objective", ""),
        context=approval.requested_action.get("context", {}),
    )
    audit_service.log(
        event_type="openhands_completed",
        event_status="completed",
        details_json=result,
        task_id=task.id,
    )
    return result


_MUTATION_AUDIT_MAP = {
    "create_branch": "github_branch_created",
    "create_patch_artifact": "github_patch_artifact_created",
    "create_pr_draft": "github_pr_created",
}


def _dispatch_github_mutation(approval, task, audit_service: AuditService) -> dict:
    github_mutation_service = GitHubMutationService()
    request_type = approval.action_name.split("github_mutation:", 1)[1]
    repo = approval.requested_action.get("repo", "unknown/repo")
    result = github_mutation_service.run(
        request_type=request_type,
        repo=repo,
        title=approval.requested_action.get("title", task.title),
        objective=approval.requested_action.get("objective", ""),
        context=approval.requested_action.get("context", {}),
    )
    event_type = _MUTATION_AUDIT_MAP.get(request_type, "github_mutation_approved")
    audit_service.log(
        event_type=event_type,
        event_status="completed",
        details_json=result,
        task_id=task.id,
    )
    return result


def _dispatch_github(approval, task, audit_service: AuditService) -> dict:
    github_service = GitHubExecutionService()
    request_type = approval.action_name.split("github:", 1)[1]
    repo = approval.requested_action.get("repo", "unknown/repo")
    result = github_service.run(
        request_type=request_type,
        repo=repo,
        title=approval.requested_action.get("title", task.title),
        objective=approval.requested_action.get("objective", ""),
        context=approval.requested_action.get("context", {}),
    )
    audit_service.log(
        event_type="github_completed",
        event_status="completed",
        details_json=result,
        task_id=task.id,
    )
    return result


def _dispatch_default(approval, task, audit_service: AuditService) -> dict:
    action_service = ActionService()
    result = action_service.run_action(
        action_name=approval.action_name,
        payload=approval.requested_action,
    )
    audit_service.log(
        event_type="action_execution",
        event_status="completed",
        details_json=result,
        task_id=task.id,
    )
    return result


_DISPATCH_TABLE = [
    ("ops:", _dispatch_ops),
    ("execution:", _dispatch_execution),
    ("github_mutation:", _dispatch_github_mutation),
    ("github:", _dispatch_github),
]


def dispatch_approved_action(approval, task, audit_service: AuditService) -> dict:
    for prefix, handler in _DISPATCH_TABLE:
        if approval.action_name.startswith(prefix):
            return handler(approval, task, audit_service)
    return _dispatch_default(approval, task, audit_service)
