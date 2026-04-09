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

    def list_memories(self, user_id: int, limit: int = 50, offset: int = 0, memory_type: str | None = None) -> list[Memory]:
        q = self.db.query(Memory).filter(Memory.user_id == user_id)
        if memory_type:
            q = q.filter(Memory.memory_type == memory_type)
        return q.order_by(Memory.id.desc()).offset(offset).limit(limit).all()

    def get_memory(self, memory_id: int) -> Memory | None:
        return self.db.query(Memory).filter(Memory.id == memory_id).first()

    def update_memory(self, memory: Memory, content: str | None = None, importance_score: int | None = None) -> Memory:
        if content is not None:
            memory.content = content
        if importance_score is not None:
            memory.importance_score = importance_score
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def delete_memory(self, memory: Memory) -> None:
        self.db.delete(memory)
        self.db.commit()

    def get_relevant_memory_snippets(self, user_id: int, limit: int = 10) -> list[str]:
        memories = (
            self.db.query(Memory)
            .filter(Memory.user_id == user_id)
            .order_by(Memory.importance_score.desc(), Memory.id.desc())
            .limit(limit)
            .all()
        )
        return [f"{m.key}: {m.content}" for m in memories]
