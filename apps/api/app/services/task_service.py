from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus

_TERMINAL_STATUSES = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}


class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, user_id: int, conversation_id: int | None, task_type: str, title: str, context_json: dict | None = None) -> Task:
        task = Task(
            user_id=user_id,
            conversation_id=conversation_id,
            task_type=task_type,
            title=title,
            status=TaskStatus.CREATED,
            current_step="created",
            context_json=context_json or {},
            result_json={}
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def list_tasks(self, limit: int = 50, offset: int = 0) -> list[Task]:
        return self.db.query(Task).order_by(Task.id.desc()).offset(offset).limit(limit).all()

    def get_task(self, task_id: int) -> Task | None:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def update_task_status(self, task: Task, status: TaskStatus, current_step: str | None = None, result_json: dict | None = None) -> Task:
        task.status = status
        if current_step is not None:
            task.current_step = current_step
        if result_json is not None:
            task.result_json = result_json
        if status in _TERMINAL_STATUSES and task.completed_at is None:
            task.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(task)
        return task
