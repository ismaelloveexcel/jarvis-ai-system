from pydantic import BaseModel


class MemoryCreateRequest(BaseModel):
    user_id: int = 1
    memory_type: str
    key: str
    content: str
    importance_score: int = 5


class MemoryResponse(BaseModel):
    id: int
    memory_type: str
    key: str
    content: str
    importance_score: int
