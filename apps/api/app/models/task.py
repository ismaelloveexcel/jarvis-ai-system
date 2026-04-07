import enum
from sqlalchemy import Enum as SQLEnum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class TaskStatus(str, enum.Enum):
    CREATED = "created"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id"), nullable=True)
    task_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.CREATED, nullable=False)
    current_step: Mapped[str | None] = mapped_column(String, nullable=True)
    context_json: Mapped[dict] = mapped_column(JSON, default=dict)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)
