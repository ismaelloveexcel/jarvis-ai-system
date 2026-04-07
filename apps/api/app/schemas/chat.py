from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    content: str
    user_id: int = 1
    conversation_id: int | None = None


class ChatMessageResponse(BaseModel):
    response: str
    task_id: int | None = None
    conversation_id: int | None = None
