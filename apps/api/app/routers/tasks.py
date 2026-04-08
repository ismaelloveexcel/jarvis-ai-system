import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.task import TaskCreateRequest, TaskResponse, TaskStatusResponse
from app.services.task_service import TaskService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[TaskResponse])
def list_tasks(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    try:
        tasks = TaskService(db).list_tasks(limit=limit, offset=offset)
        return [
            TaskResponse(
                id=t.id,
                task_type=t.task_type,
                title=t.title,
                status=t.status.value if hasattr(t.status, "value") else str(t.status),
                current_step=t.current_step,
                context_json=t.context_json or {},
                result_json=t.result_json or {},
            )
            for t in tasks
        ]
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("list_tasks failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = TaskService(db).get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(
        task_id=task.id,
        status=task.status.value if hasattr(task.status, "value") else str(task.status),
        current_step=task.current_step,
        result_json=task.result_json or {},
    )


@router.post("/", response_model=TaskResponse)
def create_task(payload: TaskCreateRequest, db: Session = Depends(get_db)):
    try:
        task = TaskService(db).create_task(
            user_id=payload.user_id,
            conversation_id=payload.conversation_id,
            task_type=payload.task_type,
            title=payload.title,
            context_json=payload.context_json,
        )

        return TaskResponse(
            id=task.id,
            task_type=task.task_type,
            title=task.title,
            status=task.status.value if hasattr(task.status, "value") else str(task.status),
            current_step=task.current_step,
            context_json=task.context_json or {},
            result_json=task.result_json or {},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("create_task failed")
        raise HTTPException(status_code=500, detail=str(exc))
