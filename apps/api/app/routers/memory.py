import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.memory import MemoryCreateRequest, MemoryResponse, MemoryUpdateRequest
from app.services.memory_service import MemoryService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[MemoryResponse])
def list_memories(user_id: int = 1, memory_type: str | None = None, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    try:
        memories = MemoryService(db).list_memories(user_id=user_id, limit=limit, offset=offset, memory_type=memory_type)
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
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("list_memories failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=MemoryResponse)
def create_memory(payload: MemoryCreateRequest, db: Session = Depends(get_db)):
    try:
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
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("create_memory failed")
        raise HTTPException(status_code=500, detail="Internal server error")


def _memory_to_response(m) -> MemoryResponse:
    return MemoryResponse(
        id=m.id, memory_type=m.memory_type, key=m.key,
        content=m.content, importance_score=m.importance_score,
    )


@router.get("/{memory_id}", response_model=MemoryResponse)
def get_memory(memory_id: int, db: Session = Depends(get_db)):
    memory = MemoryService(db).get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return _memory_to_response(memory)


@router.put("/{memory_id}", response_model=MemoryResponse)
def update_memory(memory_id: int, payload: MemoryUpdateRequest, db: Session = Depends(get_db)):
    service = MemoryService(db)
    memory = service.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    memory = service.update_memory(memory, content=payload.content, importance_score=payload.importance_score)
    return _memory_to_response(memory)


@router.delete("/{memory_id}", status_code=204)
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    service = MemoryService(db)
    memory = service.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    service.delete_memory(memory)
