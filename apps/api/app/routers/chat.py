from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.graph.orchestrator import build_orchestrator
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.services.conversation_service import ConversationService
from app.services.memory_service import MemoryService
from app.services.task_service import TaskService

router = APIRouter()


@router.post("/message", response_model=ChatMessageResponse)
def post_message(payload: ChatMessageRequest, db: Session = Depends(get_db)):
    conversation_service = ConversationService(db)
    memory_service = MemoryService(db)
    task_service = TaskService(db)

    conversation = conversation_service.get_or_create(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
    )

    conversation_service.add_message(
        conversation_id=conversation.id,
        role="user",
        content=payload.content,
    )

    memory_snippets = memory_service.get_relevant_memory_snippets(payload.user_id)

    graph = build_orchestrator()
    result = graph.invoke(
        {
            "messages": [{"role": "user", "content": payload.content}],
            "user_id": payload.user_id,
            "task_id": None,
            "context": {"memory_snippets": memory_snippets},
            "route": "",
            "final_response": "",
        }
    )

    task_id = None
    if result["route"] == "task":
        task = task_service.create_task(
            user_id=payload.user_id,
            conversation_id=conversation.id,
            task_type="general_task",
            title=payload.content[:120],
            context_json={"source": "chat"},
        )
        task_id = task.id

    conversation_service.add_message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["final_response"],
        metadata_json={"route": result["route"], "task_id": task_id},
    )

    return ChatMessageResponse(
        response=result["final_response"],
        task_id=task_id,
        conversation_id=conversation.id,
    )
