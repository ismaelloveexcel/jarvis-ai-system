from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    user_id: int = Field(default=1, ge=1)
    conversation_id: int | None = None


class ChatMessageResponse(BaseModel):
    response: str
    task_id: int | None = None
    conversation_id: int | None = None
