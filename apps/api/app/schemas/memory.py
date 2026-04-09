from pydantic import BaseModel, Field


class MemoryCreateRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    memory_type: str = Field(..., min_length=1, max_length=100)
    key: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=10000)
    importance_score: int = Field(default=5, ge=1, le=10)


class MemoryResponse(BaseModel):
    id: int
    memory_type: str
    key: str
    content: str
    importance_score: int


class MemoryUpdateRequest(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=10000)
    importance_score: int | None = Field(default=None, ge=1, le=10)
