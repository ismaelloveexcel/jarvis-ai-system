from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    action_name: Mapped[str] = mapped_column(String, nullable=False)
    requested_action: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
