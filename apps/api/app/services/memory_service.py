from sqlalchemy.orm import Session
from app.models.memory import Memory


class MemoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_memory(self, user_id: int, memory_type: str, key: str, content: str, importance_score: int = 5) -> Memory:
        memory = Memory(
            user_id=user_id,
            memory_type=memory_type,
            key=key,
            content=content,
            importance_score=importance_score
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def list_memories(self, user_id: int) -> list[Memory]:
        return (
            self.db.query(Memory)
            .filter(Memory.user_id == user_id)
            .order_by(Memory.id.desc())
            .all()
        )

    def get_relevant_memory_snippets(self, user_id: int, limit: int = 10) -> list[str]:
        memories = (
            self.db.query(Memory)
            .filter(Memory.user_id == user_id)
            .order_by(Memory.importance_score.desc(), Memory.id.desc())
            .limit(limit)
            .all()
        )
        return [f"{m.key}: {m.content}" for m in memories]
