import logging
from app.tasks.celery_app import celery_app
from app.db.session import get_background_db
from app.services.task_service import TaskService
from app.services.audit_service import AuditService
from app.services.openhands_service import OpenHandsService
from app.models.task import TaskStatus

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2)
def run_openhands_execution(
    self,
    task_id: int,
    request_type: str,
    title: str,
    objective: str,
    context: dict,
):
    """
    Celery task to execute OpenHands requests with retry logic.
    """
    db = get_background_db()
    try:
        task_service = TaskService(db)
        audit_service = AuditService(db)
        openhands_service = OpenHandsService()

        task = task_service.get_task(task_id)
        if not task:
            logger.error("OpenHands execution task %s not found", task_id)
            return

        task_service.update_task_status(
            task, TaskStatus.ANALYZING, current_step="analyzing execution"
        )
        task_service.update_task_status(
            task, TaskStatus.PLANNING, current_step="planning execution"
        )
        task_service.update_task_status(
            task, TaskStatus.EXECUTING, current_step="executing with OpenHands"
        )

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

        task_service.update_task_status(
            task, TaskStatus.COMPLETED, current_step="completed", result_json=result
        )

        audit_service.log(
            event_type="openhands_completed",
            event_status="completed",
            details_json=result,
            task_id=task.id,
        )

        return result

    except Exception as exc:
        logger.exception(
            "OpenHands execution task %s failed (attempt %s)", task_id, self.request.retries
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
                    event_type="openhands_failed",
                    event_status="failed",
                    details_json={"error": str(exc), "max_retries_exceeded": True},
                    task_id=task.id,
                )
    finally:
        db.close()
