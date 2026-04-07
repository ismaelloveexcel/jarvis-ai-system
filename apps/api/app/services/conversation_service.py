from sqlalchemy.orm import Session
from app.models.conversation import Conversation
from app.models.message import Message


class ConversationService:
    def __init__(self, db: Session):
        self.db = db

    def create_conversation(self, user_id: int, title: str | None = None) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title or "New Conversation")
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_or_create(self, user_id: int, conversation_id: int | None) -> Conversation:
        if conversation_id:
            existing = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if existing:
                return existing
        return self.create_conversation(user_id=user_id)

    def add_message(self, conversation_id: int, role: str, content: str, metadata_json: dict | None = None) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata_json=metadata_json or {}
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg
