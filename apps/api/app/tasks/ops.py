import logging
from app.tasks.celery_app import celery_app
from app.db.session import get_background_db
from app.services.task_service import TaskService
from app.services.audit_service import AuditService
from app.services.ops_service import OpsService
from app.models.task import TaskStatus

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def run_ops_request(
    self,
    task_id: int,
    request_type: str,
    title: str,
    environment: str,
    context: dict,
):
    """
    Celery task to execute ops/deployment requests with retry logic.
    """
    db = get_background_db()
    try:
        task_service = TaskService(db)
        audit_service = AuditService(db)
        ops_service = OpsService()

        task = task_service.get_task(task_id)
        if not task:
            logger.error("Ops request task %s not found", task_id)
            return

        task_service.update_task_status(
            task, TaskStatus.EXECUTING, current_step="executing ops request"
        )

        audit_service.log(
            event_type="ops_requested",
            event_status="started",
            details_json={"request_type": request_type, "environment": environment, "title": title},
            task_id=task.id,
        )

        result = ops_service.run(
            request_type=request_type,
            title=title,
            environment=environment,
            context=context,
        )

        task_service.update_task_status(
            task, TaskStatus.COMPLETED, current_step="completed", result_json=result
        )

        audit_service.log(
            event_type="ops_completed",
            event_status="completed",
            details_json=result,
            task_id=task.id,
        )

        return result

    except Exception as exc:
        logger.exception(
            "Ops request task %s failed (attempt %s)", task_id, self.request.retries
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)  # Retry in 60 seconds
        else:
            task_service = TaskService(db)
            audit_service = AuditService(db)
            task = task_service.get_task(task_id)
            if task:
                task_service.update_task_status(
                    task,
                    TaskStatus.FAILED,
                    current_step="failed",
                    result_json={"error": str(exc), "max_retries_exceeded": True},
                )
                audit_service.log(
                    event_type="ops_failed",
                    event_status="failed",
                    details_json={"error": str(exc), "max_retries_exceeded": True},
                    task_id=task.id,
                )
    finally:
        db.close()
