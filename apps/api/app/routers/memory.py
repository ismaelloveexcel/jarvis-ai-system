from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.memory import MemoryCreateRequest, MemoryResponse
from app.services.memory_service import MemoryService

router = APIRouter()


@router.get("/", response_model=list[MemoryResponse])
def list_memories(user_id: int = 1, db: Session = Depends(get_db)):
    memories = MemoryService(db).list_memories(user_id=user_id)
    return [
        MemoryResponse(
            id=m.id,
            memory_type=m.memory_type,
            key=m.key,
            content=m.content,
            importance_score=m.importance_score,
        )
        for m in memories
    ]


@router.post("/", response_model=MemoryResponse)
def create_memory(payload: MemoryCreateRequest, db: Session = Depends(get_db)):
    memory = MemoryService(db).create_memory(
        user_id=payload.user_id,
        memory_type=payload.memory_type,
        key=payload.key,
        content=payload.content,
        importance_score=payload.importance_score,
    )

    return MemoryResponse(
        id=memory.id,
        memory_type=memory.memory_type,
        key=memory.key,
        content=memory.content,
        importance_score=memory.importance_score,
    )
