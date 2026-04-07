from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.task import TaskCreateRequest, TaskResponse
from app.services.task_service import TaskService

router = APIRouter()


@router.get("/", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    tasks = TaskService(db).list_tasks()
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


@router.post("/", response_model=TaskResponse)
def create_task(payload: TaskCreateRequest, db: Session = Depends(get_db)):
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
