from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from app.models.approval import Approval

DEFAULT_EXPIRY_HOURS = 24


class ApprovalService:
    def __init__(self, db: Session):
        self.db = db

    def create_approval(self, task_id: int, action_name: str, requested_action: dict, expiry_hours: int = DEFAULT_EXPIRY_HOURS) -> Approval:
        approval = Approval(
            task_id=task_id,
            action_name=action_name,
            requested_action=requested_action,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def list_approvals(self, status: str | None = None, limit: int = 50, offset: int = 0) -> list[Approval]:
        q = self.db.query(Approval)
        if status:
            q = q.filter(Approval.status == status)
        return q.order_by(Approval.id.desc()).offset(offset).limit(limit).all()

    def get_approval(self, approval_id: int) -> Approval | None:
        return self.db.query(Approval).filter(Approval.id == approval_id).first()

    def approve(self, approval: Approval, decision_notes: str | None = None, approved_by_user_id: int | None = None) -> Approval:
        approval.status = "approved"
        approval.decision_notes = decision_notes
        approval.approved_by = approved_by_user_id
        approval.approved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def expire(self, approval: Approval, decision_notes: str | None = None) -> Approval:
        approval.status = "expired"
        approval.decision_notes = decision_notes
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def reject(self, approval: Approval, decision_notes: str | None = None) -> Approval:
        approval.status = "rejected"
        approval.decision_notes = decision_notes
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def expire_stale(self) -> int:
        """Expire all pending approvals past their expires_at. Returns count expired."""
        now = datetime.now(timezone.utc)
        stale = (
            self.db.query(Approval)
            .filter(Approval.status == "pending")
            .filter(Approval.expires_at.isnot(None))
            .filter(Approval.expires_at < now)
            .all()
        )
        for approval in stale:
            approval.status = "expired"
            approval.decision_notes = "Auto-expired: approval window elapsed"
        if stale:
            self.db.commit()
        return len(stale)
