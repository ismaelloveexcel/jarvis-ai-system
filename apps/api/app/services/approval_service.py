from sqlalchemy.orm import Session
from app.models.approval import Approval


class ApprovalService:
    def __init__(self, db: Session):
        self.db = db

    def create_approval(self, task_id: int, action_name: str, requested_action: dict) -> Approval:
        approval = Approval(
            task_id=task_id,
            action_name=action_name,
            requested_action=requested_action,
            status="pending",
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def list_approvals(self) -> list[Approval]:
        return self.db.query(Approval).order_by(Approval.id.desc()).all()

    def get_approval(self, approval_id: int) -> Approval | None:
        return self.db.query(Approval).filter(Approval.id == approval_id).first()

    def approve(self, approval: Approval, decision_notes: str | None = None) -> Approval:
        approval.status = "approved"
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
