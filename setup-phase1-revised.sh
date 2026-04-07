#!/bin/bash
# =============================================================================
# Jarvis Assistant – Phase 1 Revised Bootstrap Script
# Creates a working monorepo skeleton with:
# - Next.js frontend
# - FastAPI backend
# - PostgreSQL
# - LangGraph basic orchestration
# - persistent tasks + memories
# - provider-agnostic LLM interface
#
# Run once:
#   bash setup-phase1-revised.sh
# =============================================================================

set -euo pipefail

# FIX: Changed from "jarvis-assistant" to "." so scaffold lands directly in the
#      current repo root instead of creating a redundant nested directory.
PROJECT_ROOT="."

echo "🚀 Starting Jarvis Phase 1 revised bootstrap..."

# -----------------------------------------------------------------------------
# Create structure
# -----------------------------------------------------------------------------
mkdir -p "${PROJECT_ROOT}"/apps/api/app/{core,db,graph,models,routers,schemas,services}
mkdir -p "${PROJECT_ROOT}"/apps/web/app
mkdir -p "${PROJECT_ROOT}"/apps/web/components
mkdir -p "${PROJECT_ROOT}"/apps/web/public
mkdir -p "${PROJECT_ROOT}"/packages/{agent_core,memory,models,utils}
mkdir -p "${PROJECT_ROOT}"/infra
mkdir -p "${PROJECT_ROOT}"/postgres
mkdir -p "${PROJECT_ROOT}"/docs

echo "📁 Writing files..."

# -----------------------------------------------------------------------------
# Root files
# -----------------------------------------------------------------------------

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.pyc
.venv/
.env

# Node
node_modules/
.next/
out/

# OS / Editor
.DS_Store
.vscode/
.idea/

# Logs
*.log

# Docker volumes / temp
postgres_data/
EOF

cat > .env.example << 'EOF'
# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
APP_ENV=development
APP_NAME=Jarvis Assistant
SECRET_KEY=change-me

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
DATABASE_URL=postgresql://jarvis:changeme123@postgres:5432/jarvis_db
DATABASE_URL_LOCAL=postgresql://jarvis:changeme123@localhost:5432/jarvis_db

# -----------------------------------------------------------------------------
# LLM (provider-agnostic via LiteLLM)
# Supported providers in this Phase 1:
# openai | anthropic | xai
# -----------------------------------------------------------------------------
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=

OPENAI_API_KEY=
ANTHROPIC_API_KEY=
XAI_API_KEY=

# -----------------------------------------------------------------------------
# Frontend
# -----------------------------------------------------------------------------
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
EOF

cat > README.md << 'EOF'
# Jarvis Assistant – Phase 1 Revised

## What this phase includes
- Next.js frontend
- FastAPI backend
- PostgreSQL
- LangGraph base flow
- Persistent tasks + memories
- Provider-agnostic model interface

## Run locally

### 1. Prepare env
cp .env.example .env

Then edit `.env` and add your real `LLM_API_KEY`.

### 2. Start backend + database
docker compose up --build

### 3. Start frontend
In a separate terminal:
cd apps/web
npm install
npm run dev

### 4. Open
http://localhost:3000

## Notes
- This is Phase 1 only.
- No MCP tools yet.
- No OpenHands yet.
- No auth yet.
EOF

cat > docker-compose.yml << 'EOF'
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    container_name: jarvis-postgres
    environment:
      POSTGRES_DB: jarvis_db
      POSTGRES_USER: jarvis
      POSTGRES_PASSWORD: changeme123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: jarvis-api
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql://jarvis:changeme123@postgres:5432/jarvis_db
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# -----------------------------------------------------------------------------
# Database init
# -----------------------------------------------------------------------------

cat > postgres/init.sql << 'EOF'
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    preferences_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL,
    task_type TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    current_step TEXT,
    context_json JSONB DEFAULT '{}'::jsonb,
    result_json JSONB DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    memory_type TEXT NOT NULL,
    key TEXT NOT NULL,
    content TEXT NOT NULL,
    importance_score INTEGER DEFAULT 5,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);
EOF

# -----------------------------------------------------------------------------
# Backend files
# -----------------------------------------------------------------------------

cat > apps/api/requirements.txt << 'EOF'
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
litellm==1.52.0
langgraph==0.2.45
langchain-core==0.3.12
EOF

cat > apps/api/Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

cat > apps/api/app/__init__.py << 'EOF'
EOF

cat > apps/api/app/core/__init__.py << 'EOF'
EOF

cat > apps/api/app/core/config.py << 'EOF'
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "Jarvis Assistant"
    SECRET_KEY: str = "change-me"

    DATABASE_URL: str = "postgresql://jarvis:changeme123@localhost:5432/jarvis_db"

    LLM_PROVIDER: Literal["openai", "anthropic", "xai"] = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: str = ""

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    XAI_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
EOF

cat > apps/api/app/core/llm.py << 'EOF'
from typing import Any, Dict, List
from litellm import completion
from app.core.config import settings


def get_provider_api_key() -> str:
    if settings.LLM_API_KEY:
        return settings.LLM_API_KEY

    if settings.LLM_PROVIDER == "openai":
        return settings.OPENAI_API_KEY
    if settings.LLM_PROVIDER == "anthropic":
        return settings.ANTHROPIC_API_KEY
    if settings.LLM_PROVIDER == "xai":
        return settings.XAI_API_KEY

    return ""


def call_llm(messages: List[Dict[str, str]], temperature: float = 0.4, max_tokens: int = 800) -> str:
    api_key = get_provider_api_key()

    if not api_key:
        return "LLM is not configured yet. Add a valid API key in .env."

    model_name = f"{settings.LLM_PROVIDER}/{settings.LLM_MODEL}"

    response: Any = completion(
        model=model_name,
        messages=messages,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response["choices"][0]["message"]["content"]
EOF

cat > apps/api/app/db/__init__.py << 'EOF'
EOF

cat > apps/api/app/db/session.py << 'EOF'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF

cat > apps/api/app/models/__init__.py << 'EOF'
from app.models.base import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.task import Task, TaskStatus
from app.models.memory import Memory
EOF

cat > apps/api/app/models/base.py << 'EOF'
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
EOF

cat > apps/api/app/models/user.py << 'EOF'
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    preferences_json: Mapped[dict] = mapped_column(JSON, default=dict)
EOF

cat > apps/api/app/models/conversation.py << 'EOF'
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
EOF

cat > apps/api/app/models/message.py << 'EOF'
from sqlalchemy import ForeignKey, JSON, Text, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id"), nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
EOF

cat > apps/api/app/models/task.py << 'EOF'
import enum
from sqlalchemy import Enum as SQLEnum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class TaskStatus(str, enum.Enum):
    CREATED = "created"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id"), nullable=True)
    task_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.CREATED, nullable=False)
    current_step: Mapped[str | None] = mapped_column(String, nullable=True)
    context_json: Mapped[dict] = mapped_column(JSON, default=dict)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)
EOF

cat > apps/api/app/models/memory.py << 'EOF'
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    memory_type: Mapped[str] = mapped_column(String, nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance_score: Mapped[int] = mapped_column(default=5)
EOF

cat > apps/api/app/schemas/__init__.py << 'EOF'
EOF

cat > apps/api/app/schemas/chat.py << 'EOF'
from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    content: str
    user_id: int = 1
    conversation_id: int | None = None


class ChatMessageResponse(BaseModel):
    response: str
    task_id: int | None = None
    conversation_id: int | None = None
EOF

cat > apps/api/app/schemas/task.py << 'EOF'
from pydantic import BaseModel


class TaskCreateRequest(BaseModel):
    user_id: int = 1
    conversation_id: int | None = None
    task_type: str
    title: str
    context_json: dict = {}


class TaskResponse(BaseModel):
    id: int
    task_type: str
    title: str
    status: str
    current_step: str | None = None
    context_json: dict = {}
    result_json: dict = {}
EOF

cat > apps/api/app/schemas/memory.py << 'EOF'
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
EOF

cat > apps/api/app/services/__init__.py << 'EOF'
EOF

cat > apps/api/app/services/task_service.py << 'EOF'
from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus


class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, user_id: int, conversation_id: int | None, task_type: str, title: str, context_json: dict | None = None) -> Task:
        task = Task(
            user_id=user_id,
            conversation_id=conversation_id,
            task_type=task_type,
            title=title,
            status=TaskStatus.CREATED,
            current_step="created",
            context_json=context_json or {},
            result_json={}
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def list_tasks(self) -> list[Task]:
        return self.db.query(Task).order_by(Task.id.desc()).all()

    def get_task(self, task_id: int) -> Task | None:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def update_task_status(self, task: Task, status: TaskStatus, current_step: str | None = None, result_json: dict | None = None) -> Task:
        task.status = status
        if current_step is not None:
            task.current_step = current_step
        if result_json is not None:
            task.result_json = result_json
        self.db.commit()
        self.db.refresh(task)
        return task
EOF

cat > apps/api/app/services/memory_service.py << 'EOF'
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
EOF

cat > apps/api/app/services/conversation_service.py << 'EOF'
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
EOF

cat > apps/api/app/graph/__init__.py << 'EOF'
EOF

cat > apps/api/app/graph/orchestrator.py << 'EOF'
from typing import Annotated, Optional, TypedDict
from operator import add

from langgraph.graph import END, StateGraph

from app.core.llm import call_llm


class AgentState(TypedDict):
    messages: Annotated[list, add]
    user_id: int
    task_id: Optional[int]
    context: dict
    route: str
    final_response: str


def intake_node(state: AgentState):
    return state


def context_node(state: AgentState):
    return state


def classify_node(state: AgentState):
    user_text = state["messages"][-1]["content"].lower()

    task_keywords = ["build", "create app", "generate plan", "set up", "implement", "design system"]
    if any(k in user_text for k in task_keywords):
        state["route"] = "task"
    else:
        state["route"] = "chat"

    return state


def plan_node(state: AgentState):
    if state["route"] == "task":
        state["final_response"] = "Task recognized. Phase 1 can create and track the task, but execution tooling is not added yet."
        return state

    memory_lines = state.get("context", {}).get("memory_snippets", [])
    memory_context = "\n".join(memory_lines) if memory_lines else "No memory context available."

    system_prompt = (
        "You are Jarvis Assistant Phase 1. "
        "Be concise, useful, structured, and execution-oriented. "
        "If asked to perform an action beyond current Phase 1 capabilities, say so clearly."
    )

    user_prompt = f"Memory context:\n{memory_context}\n\nUser request:\n{state['messages'][-1]['content']}"
    response = call_llm(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    state["final_response"] = response
    return state


def execute_node(state: AgentState):
    return state


def complete_node(state: AgentState):
    return state


def build_orchestrator():
    graph = StateGraph(AgentState)

    graph.add_node("intake", intake_node)
    graph.add_node("context", context_node)
    graph.add_node("classify", classify_node)
    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("complete", complete_node)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "context")
    graph.add_edge("context", "classify")
    graph.add_edge("classify", "plan")
    graph.add_edge("plan", "execute")
    graph.add_edge("execute", "complete")
    graph.add_edge("complete", END)

    return graph.compile()
EOF

cat > apps/api/app/routers/__init__.py << 'EOF'
EOF

cat > apps/api/app/routers/chat.py << 'EOF'
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
EOF

cat > apps/api/app/routers/tasks.py << 'EOF'
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.task import TaskCreateRequest, TaskResponse
from app.services.task_service import TaskService

router = APIRouter()


@router.get("/", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    tasks = TaskService(db).list_tasks()
    return [
        TaskResponse(
            id=t.id,
            task_type=t.task_type,
            title=t.title,
            status=t.status.value if hasattr(t.status, "value") else str(t.status),
            current_step=t.current_step,
            context_json=t.context_json or {},
            result_json=t.result_json or {},
        )
        for t in tasks
    ]


@router.post("/", response_model=TaskResponse)
def create_task(payload: TaskCreateRequest, db: Session = Depends(get_db)):
    task = TaskService(db).create_task(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        task_type=payload.task_type,
        title=payload.title,
        context_json=payload.context_json,
    )

    return TaskResponse(
        id=task.id,
        task_type=task.task_type,
        title=task.title,
        status=task.status.value if hasattr(task.status, "value") else str(task.status),
        current_step=task.current_step,
        context_json=task.context_json or {},
        result_json=task.result_json or {},
    )
EOF

cat > apps/api/app/routers/memory.py << 'EOF'
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
EOF

cat > apps/api/app/main.py << 'EOF'
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import chat, memory, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME} in {settings.APP_ENV}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])


@app.get("/")
def root():
    return {"status": "healthy", "app": settings.APP_NAME, "version": "0.1.0"}
EOF

# -----------------------------------------------------------------------------
# Frontend files
# -----------------------------------------------------------------------------

cat > apps/web/package.json << 'EOF'
{
  "name": "jarvis-web",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.2.13",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/node": "^20.16.10",
    "@types/react": "^18.3.5",
    "@types/react-dom": "^18.3.0",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.13",
    "typescript": "^5.6.2"
  }
}
EOF

cat > apps/web/next.config.mjs << 'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true
};

export default nextConfig;
EOF

cat > apps/web/tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
EOF

cat > apps/web/next-env.d.ts << 'EOF'
/// <reference types="next" />
/// <reference types="next/image-types/global" />

// This file should not be edited manually.
EOF

cat > apps/web/postcss.config.js << 'EOF'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
EOF

cat > apps/web/tailwind.config.ts << 'EOF'
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
EOF

cat > apps/web/app/globals.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body {
  margin: 0;
  padding: 0;
  font-family: system-ui, -apple-system, sans-serif;
  background: #09090b;
  color: #fafafa;
}
EOF

cat > apps/web/app/layout.tsx << 'EOF'
import "./globals.css";

export const metadata = {
  title: "Jarvis Assistant",
  description: "Jarvis Assistant Phase 1"
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
EOF

cat > apps/web/components/Sidebar.tsx << 'EOF'
export default function Sidebar() {
  return (
    <div className="w-72 bg-zinc-900 border-r border-zinc-800 p-4">
      <h1 className="text-xl font-semibold mb-6">Jarvis</h1>
      <div className="space-y-2">
        <div className="px-4 py-2 bg-zinc-800 rounded-lg">Conversations</div>
        <div className="px-4 py-2 rounded-lg text-zinc-400">Tasks</div>
        <div className="px-4 py-2 rounded-lg text-zinc-400">Memory</div>
      </div>
    </div>
  );
}
EOF

cat > apps/web/components/RightPanel.tsx << 'EOF'
type Props = {
  taskId: number | null;
  conversationId: number | null;
};

export default function RightPanel({ taskId, conversationId }: Props) {
  return (
    <div className="w-80 bg-zinc-900 border-l border-zinc-800 p-4">
      <h2 className="text-lg font-semibold mb-4">Run Context</h2>
      <div className="space-y-3 text-sm text-zinc-300">
        <div className="bg-zinc-800 rounded-xl p-3">
          <div className="text-zinc-400">Conversation ID</div>
          <div>{conversationId ?? "—"}</div>
        </div>
        <div className="bg-zinc-800 rounded-xl p-3">
          <div className="text-zinc-400">Task ID</div>
          <div>{taskId ?? "—"}</div>
        </div>
        <div className="bg-zinc-800 rounded-xl p-3">
          <div className="text-zinc-400">Phase</div>
          <div>Phase 1</div>
        </div>
      </div>
    </div>
  );
}
EOF

cat > apps/web/app/page.tsx << 'EOF'
"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import RightPanel from "@/components/RightPanel";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export default function HomePage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hello. I'm Jarvis Phase 1. I can chat, create tasks, and remember entries." }
  ]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [taskId, setTaskId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${apiBase}/chat/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          content: trimmed,
          user_id: 1,
          conversation_id: conversationId
        })
      });

      if (!res.ok) {
        throw new Error("Failed to send message");
      }

      const data = await res.json();

      setConversationId(data.conversation_id ?? null);
      setTaskId(data.task_id ?? null);

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response }
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong while contacting the backend." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      <Sidebar />

      <main className="flex-1 flex flex-col bg-zinc-950">
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-2xl px-4 py-3 rounded-2xl ${
                  msg.role === "user" ? "bg-blue-600" : "bg-zinc-800"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
        </div>

        <div className="border-t border-zinc-800 bg-zinc-900 p-4">
          <div className="flex gap-2">
            <input
              className="flex-1 rounded-2xl bg-zinc-800 border border-zinc-700 px-4 py-3 outline-none"
              type="text"
              value={input}
              placeholder="Ask Jarvis something..."
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") sendMessage();
              }}
            />
            <button
              className="rounded-2xl bg-blue-600 px-6 py-3 font-medium disabled:opacity-50"
              onClick={sendMessage}
              disabled={loading}
            >
              {loading ? "Sending..." : "Send"}
            </button>
          </div>
        </div>
      </main>

      <RightPanel taskId={taskId} conversationId={conversationId} />
    </div>
  );
}
EOF

# -----------------------------------------------------------------------------
# Docs
# -----------------------------------------------------------------------------

cat > docs/phase1-scope.md << 'EOF'
# Phase 1 Scope

Included:
- chat UI
- FastAPI backend
- PostgreSQL
- basic LangGraph routing
- task persistence
- memory persistence

Excluded:
- MCP tools
- OpenHands integration
- approvals
- auth
- deployment pipelines
EOF

# -----------------------------------------------------------------------------
# Final output
# -----------------------------------------------------------------------------

echo ""
echo "✅ Phase 1 revised skeleton created successfully."
echo ""
echo "Next steps:"
echo "1. cp .env.example .env"
echo "2. Edit .env and set a real LLM_API_KEY"
echo "3. docker compose up --build"
echo "4. In another terminal:"
echo "   cd apps/web && npm install && npm run dev"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Phase 1 complete."
