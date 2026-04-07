#!/bin/bash
# =============================================================================
# Jarvis Assistant – Phase 2 Bootstrap Script
# Adds:
# - action engine
# - tool layer
# - task execution routing
# - first executable actions
# - task status updates
#
# Assumes Phase 1 already exists in current repo root.
# Run once:
#   bash setup-phase2.sh
#
# FIXES vs original script:
# 1. Tools/actions placed under apps/api/app/ (inside Docker build context)
#    instead of packages/ which is unreachable from the container.
# 2. Imports use app.tools.* / app.actions.* for Docker compatibility.
# 3. SAFE_BASE_DIR uses env var with fallback for Docker vs local.
# 4. docker-compose.yml updated with workspace volume mount.
# 5. packages/ created as empty placeholders for future extraction.
# =============================================================================

set -euo pipefail

PROJECT_ROOT="."

cd "${PROJECT_ROOT}"

echo "🚀 Starting Jarvis Phase 2 bootstrap..."

# -----------------------------------------------------------------------------
# Create new Phase 2 structure
# -----------------------------------------------------------------------------
mkdir -p packages/actions
mkdir -p packages/tools
mkdir -p packages/tasks
mkdir -p workspace/generated
mkdir -p apps/api/app/tools
mkdir -p apps/api/app/actions

# -----------------------------------------------------------------------------
# Root gitignore update (append safe workspace rule if missing)
# -----------------------------------------------------------------------------
if ! grep -q "workspace/generated" .gitignore; then
  cat >> .gitignore << 'EOF'

# Jarvis local generated outputs
workspace/generated/*
!workspace/generated/.gitkeep
EOF
fi

touch workspace/generated/.gitkeep

# -----------------------------------------------------------------------------
# Backend requirements update
# -----------------------------------------------------------------------------
if ! grep -q "^requests==" apps/api/requirements.txt; then
  echo "requests==2.32.3" >> apps/api/requirements.txt
fi

# -----------------------------------------------------------------------------
# Shared package placeholder init files
# -----------------------------------------------------------------------------
touch packages/actions/__init__.py
touch packages/tools/__init__.py
touch packages/tasks/__init__.py

# -----------------------------------------------------------------------------
# Tools layer (inside apps/api/app/ for Docker compatibility)
# -----------------------------------------------------------------------------

cat > apps/api/app/tools/__init__.py << 'EOF'
EOF

cat > apps/api/app/tools/filesystem_tool.py << 'EOF'
import os
from pathlib import Path

# Inside Docker: /app/workspace (mounted volume)
# Local dev: repo_root/workspace/generated
_env_base = os.environ.get("JARVIS_WORKSPACE_DIR", "")
if _env_base:
    SAFE_BASE_DIR = Path(_env_base)
else:
    SAFE_BASE_DIR = Path(__file__).resolve().parents[3] / "workspace" / "generated"

SAFE_BASE_DIR.mkdir(parents=True, exist_ok=True)


def safe_write_file(relative_path: str, content: str) -> dict:
    target = (SAFE_BASE_DIR / relative_path).resolve()

    if not str(target).startswith(str(SAFE_BASE_DIR.resolve())):
        raise ValueError("Unsafe path detected")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return {
        "status": "success",
        "action": "create_file",
        "path": str(target),
        "bytes_written": len(content.encode("utf-8")),
    }


def safe_read_file(relative_path: str) -> dict:
    target = (SAFE_BASE_DIR / relative_path).resolve()

    if not str(target).startswith(str(SAFE_BASE_DIR.resolve())):
        raise ValueError("Unsafe path detected")

    if not target.exists():
        raise FileNotFoundError(f"File not found: {relative_path}")

    content = target.read_text(encoding="utf-8")
    return {
        "status": "success",
        "action": "read_file",
        "path": str(target),
        "content": content,
    }
EOF

cat > apps/api/app/tools/http_tool.py << 'EOF'
import requests


def safe_http_get(url: str, timeout: int = 15) -> dict:
    response = requests.get(url, timeout=timeout)
    return {
        "status": "success",
        "action": "http_request",
        "url": url,
        "status_code": response.status_code,
        "content_preview": response.text[:1000],
    }
EOF

cat > apps/api/app/tools/github_tool.py << 'EOF'
def github_repo_info_stub(repo: str) -> dict:
    return {
        "status": "success",
        "action": "github_repo_info_stub",
        "repo": repo,
        "note": "Phase 2 safe stub only. No live GitHub mutation is performed.",
        "mock_data": {
            "name": repo.split("/")[-1] if "/" in repo else repo,
            "owner": repo.split("/")[0] if "/" in repo else "unknown",
            "stars": 0,
            "language": "unknown",
            "description": "Stub response - connect to real GitHub API in Phase 3",
        },
    }
EOF

# -----------------------------------------------------------------------------
# Actions layer (inside apps/api/app/ for Docker compatibility)
# -----------------------------------------------------------------------------

cat > apps/api/app/actions/__init__.py << 'EOF'
EOF

cat > apps/api/app/actions/action_registry.py << 'EOF'
from app.tools.filesystem_tool import safe_write_file, safe_read_file
from app.tools.http_tool import safe_http_get
from app.tools.github_tool import github_repo_info_stub

AVAILABLE_ACTIONS = [
    {
        "name": "create_file",
        "description": "Create or overwrite a file under the controlled workspace directory",
        "required_params": ["relative_path", "content"],
    },
    {
        "name": "read_file",
        "description": "Read a file from the controlled workspace directory",
        "required_params": ["relative_path"],
    },
    {
        "name": "http_request",
        "description": "Perform a safe outbound HTTP GET request",
        "required_params": ["url"],
    },
    {
        "name": "github_repo_info_stub",
        "description": "Return structured stub info for a GitHub repo (no real API call)",
        "required_params": ["repo"],
    },
]


class ActionRegistry:
    def list_actions(self) -> list[dict]:
        return AVAILABLE_ACTIONS

    def execute(self, action_name: str, payload: dict) -> dict:
        if action_name == "create_file":
            return safe_write_file(
                relative_path=payload["relative_path"],
                content=payload["content"],
            )

        if action_name == "read_file":
            return safe_read_file(
                relative_path=payload["relative_path"],
            )

        if action_name == "http_request":
            return safe_http_get(
                url=payload["url"],
                timeout=payload.get("timeout", 15),
            )

        if action_name == "github_repo_info_stub":
            return github_repo_info_stub(
                repo=payload["repo"],
            )

        raise ValueError(f"Unknown action: {action_name}")
EOF

# -----------------------------------------------------------------------------
# Backend schema updates
# -----------------------------------------------------------------------------

cat > apps/api/app/schemas/action.py << 'EOF'
from pydantic import BaseModel
from typing import Any


class ActionRequest(BaseModel):
    user_id: int = 1
    conversation_id: int | None = None
    action_name: str
    payload: dict[str, Any]


class ActionResponse(BaseModel):
    task_id: int | None = None
    action_name: str
    result: dict[str, Any]
EOF

# -----------------------------------------------------------------------------
# Backend service updates
# -----------------------------------------------------------------------------

cat > apps/api/app/services/action_service.py << 'EOF'
from app.actions.action_registry import ActionRegistry


class ActionService:
    def __init__(self):
        self.registry = ActionRegistry()

    def list_actions(self) -> list[dict]:
        return self.registry.list_actions()

    def run_action(self, action_name: str, payload: dict) -> dict:
        return self.registry.execute(action_name=action_name, payload=payload)
EOF

# Keep task_service.py unchanged (Phase 1 version is correct)

# -----------------------------------------------------------------------------
# LangGraph update
# -----------------------------------------------------------------------------

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


def enrich_context_node(state: AgentState):
    return state


def classify_node(state: AgentState):
    user_text = state["messages"][-1]["content"].lower()

    action_keywords = [
        "create file", "write file", "make file",
        "fetch url", "call api", "http get",
        "github repo", "repo info",
    ]
    task_keywords = [
        "build", "create app", "generate plan",
        "set up", "implement", "design system",
    ]

    if any(k in user_text for k in action_keywords):
        state["route"] = "action"
    elif any(k in user_text for k in task_keywords):
        state["route"] = "task"
    else:
        state["route"] = "chat"

    return state


def plan_node(state: AgentState):
    if state["route"] == "task":
        state["final_response"] = (
            "Task recognized. This request has been tracked. "
            "Use the /actions endpoint to execute controlled actions in Phase 2."
        )
        return state

    if state["route"] == "action":
        state["final_response"] = (
            "Action recognized. Use the /actions endpoint to execute it. "
            "Available actions: create_file, read_file, http_request, github_repo_info_stub."
        )
        return state

    memory_lines = state.get("context", {}).get("memory_snippets", [])
    memory_context = "\n".join(memory_lines) if memory_lines else "No memory context available."

    system_prompt = (
        "You are Jarvis Assistant Phase 2. "
        "Be concise, useful, structured, and execution-oriented. "
        "If asked to perform an action beyond current Phase 2 capabilities, say so clearly."
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
    graph.add_node("enrich_context", enrich_context_node)
    graph.add_node("classify", classify_node)
    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("complete", complete_node)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "enrich_context")
    graph.add_edge("enrich_context", "classify")
    graph.add_edge("classify", "plan")
    graph.add_edge("plan", "execute")
    graph.add_edge("execute", "complete")
    graph.add_edge("complete", END)

    return graph.compile()
EOF

# -----------------------------------------------------------------------------
# New action router
# -----------------------------------------------------------------------------

cat > apps/api/app/routers/actions.py << 'EOF'
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.action import ActionRequest, ActionResponse
from app.services.action_service import ActionService
from app.services.task_service import TaskService
from app.models.task import TaskStatus

router = APIRouter()


@router.get("/available")
def list_available_actions():
    return ActionService().list_actions()


@router.post("/", response_model=ActionResponse)
def run_action(payload: ActionRequest, db: Session = Depends(get_db)):
    task_service = TaskService(db)
    action_service = ActionService()

    task = task_service.create_task(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        task_type="action",
        title=f"Action: {payload.action_name}",
        context_json={"action_name": payload.action_name, "payload": payload.payload},
    )

    try:
        task_service.update_task_status(task, TaskStatus.ANALYZING, current_step="analyzing action")
        task_service.update_task_status(task, TaskStatus.PLANNING, current_step="planning action")
        task_service.update_task_status(task, TaskStatus.EXECUTING, current_step="executing action")

        result = action_service.run_action(
            action_name=payload.action_name,
            payload=payload.payload,
        )

        task_service.update_task_status(
            task,
            TaskStatus.COMPLETED,
            current_step="completed",
            result_json=result,
        )

        return ActionResponse(
            task_id=task.id,
            action_name=payload.action_name,
            result=result,
        )
    except Exception as exc:
        task_service.update_task_status(
            task,
            TaskStatus.FAILED,
            current_step="failed",
            result_json={"error": str(exc)},
        )
        return ActionResponse(
            task_id=task.id,
            action_name=payload.action_name,
            result={"status": "failed", "error": str(exc)},
        )
EOF

# -----------------------------------------------------------------------------
# Main app update (add actions router)
# -----------------------------------------------------------------------------

cat > apps/api/app/main.py << 'EOF'
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import actions, chat, memory, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME} in {settings.APP_ENV}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.2.0",
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
app.include_router(actions.router, prefix="/actions", tags=["actions"])


@app.get("/")
def root():
    return {"status": "healthy", "app": settings.APP_NAME, "version": "0.2.0"}
EOF

# -----------------------------------------------------------------------------
# Update docker-compose.yml to mount workspace volume
# -----------------------------------------------------------------------------

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
      JARVIS_WORKSPACE_DIR: /app/workspace
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    volumes:
      - ./workspace/generated:/app/workspace
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# -----------------------------------------------------------------------------
# Frontend update
# -----------------------------------------------------------------------------

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
    { role: "assistant", content: "Hello. I'm Jarvis Phase 2. I can chat, track tasks, and execute controlled actions." }
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: trimmed,
          user_id: 1,
          conversation_id: conversationId,
        }),
      });

      const data = await res.json();
      setConversationId(data.conversation_id ?? null);
      setTaskId(data.task_id ?? null);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong while contacting the backend." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const runAction = async (actionName: string, payload: Record<string, unknown>) => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/actions/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: 1,
          conversation_id: conversationId,
          action_name: actionName,
          payload,
        }),
      });

      const data = await res.json();
      setTaskId(data.task_id ?? null);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `**Action: ${data.action_name}** (Task #${data.task_id})\n\`\`\`json\n${JSON.stringify(data.result, null, 2)}\n\`\`\``,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Action "${actionName}" failed.` },
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
                className={`max-w-2xl px-4 py-3 rounded-2xl whitespace-pre-wrap ${
                  msg.role === "user" ? "bg-blue-600" : "bg-zinc-800"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
        </div>

        <div className="border-t border-zinc-800 bg-zinc-900 p-4 space-y-3">
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
              {loading ? "..." : "Send"}
            </button>
          </div>

          <div className="flex gap-2 flex-wrap">
            <button
              className="rounded-xl bg-zinc-800 border border-zinc-700 px-4 py-2 text-sm hover:bg-zinc-700 disabled:opacity-50"
              onClick={() =>
                runAction("create_file", {
                  relative_path: "example/hello.txt",
                  content: "Hello from Jarvis Phase 2!\nGenerated at: " + new Date().toISOString(),
                })
              }
              disabled={loading}
            >
              Create File
            </button>
            <button
              className="rounded-xl bg-zinc-800 border border-zinc-700 px-4 py-2 text-sm hover:bg-zinc-700 disabled:opacity-50"
              onClick={() =>
                runAction("http_request", {
                  url: "https://httpbin.org/get",
                })
              }
              disabled={loading}
            >
              HTTP GET
            </button>
            <button
              className="rounded-xl bg-zinc-800 border border-zinc-700 px-4 py-2 text-sm hover:bg-zinc-700 disabled:opacity-50"
              onClick={() =>
                runAction("github_repo_info_stub", {
                  repo: "anthropics/claude-code",
                })
              }
              disabled={loading}
            >
              GitHub Stub
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
# Docs update
# -----------------------------------------------------------------------------

cat > docs/phase2-scope.md << 'EOF'
# Phase 2 Scope

Included:
- action engine with registry
- tool layer (filesystem, http, github stub)
- task execution routing (chat / task / action)
- create_file action (sandboxed to workspace/generated/)
- read_file action
- http_request action (GET only)
- github_repo_info_stub action
- task status lifecycle (created → analyzing → planning → executing → completed/failed)
- /actions/ API endpoint
- /actions/available endpoint
- minimal frontend action buttons

Excluded:
- MCP
- OpenHands
- approvals
- auth
- destructive GitHub execution
EOF

echo ""
echo "✅ Phase 2 files written."
echo ""
echo "Next:"
echo "1. docker compose up --build -d"
echo "2. in apps/web: npm run dev"
echo "3. test POST /actions/"
echo ""
echo "Phase 2 bootstrap complete."
