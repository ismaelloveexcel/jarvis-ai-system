#!/bin/bash
# =============================================================================
# Jarvis Assistant – Phase 3 Bootstrap Script
# Adds:
# - approval workflow
# - guardrails
# - audit logging
# - approval-aware action execution
# - MCP-ready abstraction layer
#
# Assumes Phase 2 already exists in current repo root.
# Run once:
#   bash setup-phase3.sh
#
# FIXES vs original script:
# 1. Guardrails: added read_file to policy (was falling through to "blocked").
# 2. /actions/available: preserved Phase 2 format using ActionService.list_actions().
# 3. Kept Phase 2 action_registry.py unchanged (already correct).
# =============================================================================

set -euo pipefail

PROJECT_ROOT="."
cd "${PROJECT_ROOT}"

echo "🚀 Starting Jarvis Phase 3 bootstrap..."

mkdir -p apps/api/app/guardrails
mkdir -p apps/api/app/mcp

cat > apps/api/app/guardrails/__init__.py << 'EOF'
EOF

cat > apps/api/app/mcp/__init__.py << 'EOF'
EOF

# -----------------------------------------------------------------------------
# DB schema extension (appended to init.sql)
# -----------------------------------------------------------------------------

if ! grep -q "CREATE TABLE IF NOT EXISTS approvals" postgres/init.sql; then
cat >> postgres/init.sql << 'EOF'

-- Phase 3 tables

CREATE TABLE IF NOT EXISTS approvals (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    action_name TEXT NOT NULL,
    requested_action JSONB DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending',
    decision_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    event_status TEXT NOT NULL,
    details_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_approvals_task_id ON approvals(task_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_task_id ON audit_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
EOF
fi

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

cat > apps/api/app/models/approval.py << 'EOF'
from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    action_name: Mapped[str] = mapped_column(String, nullable=False)
    requested_action: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
EOF

cat > apps/api/app/models/audit_log.py << 'EOF'
from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    event_status: Mapped[str] = mapped_column(String, nullable=False)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
EOF

cat > apps/api/app/models/__init__.py << 'EOF'
from app.models.base import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.task import Task, TaskStatus
from app.models.memory import Memory
from app.models.approval import Approval
from app.models.audit_log import AuditLog
EOF

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------

cat > apps/api/app/schemas/approval.py << 'EOF'
from pydantic import BaseModel


class ApprovalResponse(BaseModel):
    id: int
    task_id: int
    action_name: str
    requested_action: dict
    status: str
    decision_notes: str | None = None


class ApprovalDecisionRequest(BaseModel):
    decision_notes: str | None = None
EOF

cat > apps/api/app/schemas/audit_log.py << 'EOF'
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    task_id: int | None = None
    event_type: str
    event_status: str
    details_json: dict
EOF

# -----------------------------------------------------------------------------
# MCP-ready abstraction
# -----------------------------------------------------------------------------

cat > apps/api/app/mcp/base.py << 'EOF'
class MCPToolAdapter:
    """
    Phase 3 MCP-ready abstraction.
    Real MCP integration comes in Phase 4.
    This provides the interface contract future MCP tools will implement.
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name

    def invoke(self, payload: dict) -> dict:
        return {
            "status": "not_implemented",
            "tool_name": self.tool_name,
            "note": "MCP-ready abstraction only. Real MCP integration in Phase 4.",
        }

    def describe(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "parameters": {},
            "description": "MCP tool stub",
        }
EOF

# -----------------------------------------------------------------------------
# Guardrails
# FIX: Added read_file to allow list (original script missed it, causing
# it to fall through to "blocked" for unknown actions).
# -----------------------------------------------------------------------------

cat > apps/api/app/guardrails/policy.py << 'EOF'
ALLOWED_HTTP_HOSTS = {
    "example.com",
    "httpbin.org",
    "jsonplaceholder.typicode.com",
}

APPROVAL_REQUIRED_ACTIONS = {
    "create_file",
}

BLOCKED_ACTIONS = {
    "github_mutation",
    "delete_file",
    "run_shell_command",
}

SAFE_WRITE_PREFIXES = [
    "example/",
    "notes/",
    "drafts/",
]

# Actions that are always allowed without approval
ALWAYS_ALLOWED_ACTIONS = {
    "read_file",
    "github_repo_info_stub",
}
EOF

cat > apps/api/app/guardrails/service.py << 'EOF'
from urllib.parse import urlparse
from app.guardrails.policy import (
    ALLOWED_HTTP_HOSTS,
    ALWAYS_ALLOWED_ACTIONS,
    BLOCKED_ACTIONS,
    SAFE_WRITE_PREFIXES,
)


class GuardrailResult(dict):
    pass


class GuardrailService:
    def evaluate(self, action_name: str, payload: dict) -> GuardrailResult:
        if action_name in BLOCKED_ACTIONS:
            return GuardrailResult({
                "decision": "blocked",
                "reason": f"Action '{action_name}' is blocked by policy.",
            })

        if action_name in ALWAYS_ALLOWED_ACTIONS:
            return GuardrailResult({"decision": "allow"})

        if action_name == "http_request":
            url = payload.get("url", "")
            hostname = urlparse(url).hostname or ""
            if hostname not in ALLOWED_HTTP_HOSTS:
                return GuardrailResult({
                    "decision": "blocked",
                    "reason": f"HTTP host '{hostname}' is not allowlisted.",
                })
            return GuardrailResult({"decision": "allow"})

        if action_name == "create_file":
            relative_path = payload.get("relative_path", "")
            if any(relative_path.startswith(prefix) for prefix in SAFE_WRITE_PREFIXES):
                return GuardrailResult({"decision": "allow"})
            return GuardrailResult({
                "decision": "approval_required",
                "reason": f"Writing to '{relative_path}' requires approval.",
            })

        return GuardrailResult({
            "decision": "blocked",
            "reason": f"Unknown or unapproved action '{action_name}'.",
        })
EOF

# -----------------------------------------------------------------------------
# Services
# -----------------------------------------------------------------------------

cat > apps/api/app/services/audit_service.py << 'EOF'
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(self, event_type: str, event_status: str, details_json: dict, task_id: int | None = None) -> AuditLog:
        record = AuditLog(
            task_id=task_id,
            event_type=event_type,
            event_status=event_status,
            details_json=details_json,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_logs(self) -> list[AuditLog]:
        return self.db.query(AuditLog).order_by(AuditLog.id.desc()).all()
EOF

cat > apps/api/app/services/approval_service.py << 'EOF'
from sqlalchemy.orm import Session
from app.models.approval import Approval


class ApprovalService:
    def __init__(self, db: Session):
        self.db = db

    def create_approval(self, task_id: int, action_name: str, requested_action: dict) -> Approval:
        approval = Approval(
            task_id=task_id,
            action_name=action_name,
            requested_action=requested_action,
            status="pending",
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def list_approvals(self) -> list[Approval]:
        return self.db.query(Approval).order_by(Approval.id.desc()).all()

    def get_approval(self, approval_id: int) -> Approval | None:
        return self.db.query(Approval).filter(Approval.id == approval_id).first()

    def approve(self, approval: Approval, decision_notes: str | None = None) -> Approval:
        approval.status = "approved"
        approval.decision_notes = decision_notes
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def reject(self, approval: Approval, decision_notes: str | None = None) -> Approval:
        approval.status = "rejected"
        approval.decision_notes = decision_notes
        self.db.commit()
        self.db.refresh(approval)
        return approval
EOF

# action_service.py stays the same as Phase 2 (already correct)

# -----------------------------------------------------------------------------
# Routers
# -----------------------------------------------------------------------------

cat > apps/api/app/routers/approvals.py << 'EOF'
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.approval import ApprovalDecisionRequest, ApprovalResponse
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.services.task_service import TaskService
from app.services.action_service import ActionService
from app.models.task import TaskStatus

router = APIRouter()


@router.get("/", response_model=list[ApprovalResponse])
def list_approvals(db: Session = Depends(get_db)):
    approvals = ApprovalService(db).list_approvals()
    return [
        ApprovalResponse(
            id=a.id,
            task_id=a.task_id,
            action_name=a.action_name,
            requested_action=a.requested_action or {},
            status=a.status,
            decision_notes=a.decision_notes,
        )
        for a in approvals
    ]


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve_approval(approval_id: int, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)):
    approval_service = ApprovalService(db)
    audit_service = AuditService(db)
    task_service = TaskService(db)
    action_service = ActionService()

    approval = approval_service.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Approval already {approval.status}")

    approval = approval_service.approve(approval, payload.decision_notes)
    audit_service.log(
        event_type="approval",
        event_status="approved",
        details_json={"approval_id": approval.id, "action_name": approval.action_name},
        task_id=approval.task_id,
    )

    task = task_service.get_task(approval.task_id)
    if task:
        try:
            task_service.update_task_status(task, TaskStatus.EXECUTING, current_step="executing after approval")
            result = action_service.run_action(
                action_name=approval.action_name,
                payload=approval.requested_action,
            )
            task_service.update_task_status(task, TaskStatus.COMPLETED, current_step="completed", result_json=result)
            audit_service.log(
                event_type="action_execution",
                event_status="completed",
                details_json=result,
                task_id=task.id,
            )
        except Exception as exc:
            task_service.update_task_status(
                task, TaskStatus.FAILED, current_step="failed", result_json={"error": str(exc)}
            )
            audit_service.log(
                event_type="action_execution",
                event_status="failed",
                details_json={"error": str(exc)},
                task_id=task.id,
            )

    return ApprovalResponse(
        id=approval.id,
        task_id=approval.task_id,
        action_name=approval.action_name,
        requested_action=approval.requested_action or {},
        status=approval.status,
        decision_notes=approval.decision_notes,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def reject_approval(approval_id: int, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)):
    approval_service = ApprovalService(db)
    audit_service = AuditService(db)
    task_service = TaskService(db)

    approval = approval_service.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Approval already {approval.status}")

    approval = approval_service.reject(approval, payload.decision_notes)
    audit_service.log(
        event_type="approval",
        event_status="rejected",
        details_json={"approval_id": approval.id, "action_name": approval.action_name},
        task_id=approval.task_id,
    )

    task = task_service.get_task(approval.task_id)
    if task:
        task_service.update_task_status(
            task,
            TaskStatus.FAILED,
            current_step="rejected",
            result_json={"status": "rejected", "reason": approval.decision_notes or "Approval rejected"},
        )

    return ApprovalResponse(
        id=approval.id,
        task_id=approval.task_id,
        action_name=approval.action_name,
        requested_action=approval.requested_action or {},
        status=approval.status,
        decision_notes=approval.decision_notes,
    )
EOF

cat > apps/api/app/routers/audit_logs.py << 'EOF'
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(db: Session = Depends(get_db)):
    logs = AuditService(db).list_logs()
    return [
        AuditLogResponse(
            id=log.id,
            task_id=log.task_id,
            event_type=log.event_type,
            event_status=log.event_status,
            details_json=log.details_json or {},
        )
        for log in logs
    ]
EOF

cat > apps/api/app/routers/actions.py << 'EOF'
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.action import ActionRequest, ActionResponse
from app.services.action_service import ActionService
from app.services.task_service import TaskService
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.guardrails.service import GuardrailService
from app.models.task import TaskStatus

router = APIRouter()


@router.get("/available")
def list_available_actions():
    return ActionService().list_actions()


@router.post("/", response_model=ActionResponse)
def run_action(payload: ActionRequest, db: Session = Depends(get_db)):
    task_service = TaskService(db)
    action_service = ActionService()
    approval_service = ApprovalService(db)
    audit_service = AuditService(db)
    guardrail_service = GuardrailService()

    task = task_service.create_task(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        task_type="action",
        title=f"Action: {payload.action_name}",
        context_json={"action_name": payload.action_name, "payload": payload.payload},
    )

    audit_service.log(
        event_type="action_requested",
        event_status="received",
        details_json={"action_name": payload.action_name, "payload": payload.payload},
        task_id=task.id,
    )

    try:
        # Guardrail evaluation
        task_service.update_task_status(task, TaskStatus.ANALYZING, current_step="guardrail evaluation")
        guardrail = guardrail_service.evaluate(payload.action_name, payload.payload)

        # BLOCKED
        if guardrail["decision"] == "blocked":
            task_service.update_task_status(
                task,
                TaskStatus.FAILED,
                current_step="blocked",
                result_json={"status": "blocked", "reason": guardrail["reason"]},
            )
            audit_service.log(
                event_type="action_blocked",
                event_status="blocked",
                details_json={"action_name": payload.action_name, "reason": guardrail["reason"]},
                task_id=task.id,
            )
            return ActionResponse(
                task_id=task.id,
                action_name=payload.action_name,
                result={"status": "blocked", "reason": guardrail["reason"]},
            )

        # APPROVAL REQUIRED
        if guardrail["decision"] == "approval_required":
            task_service.update_task_status(
                task, TaskStatus.WAITING_FOR_APPROVAL, current_step="waiting_for_approval"
            )
            approval = approval_service.create_approval(
                task_id=task.id,
                action_name=payload.action_name,
                requested_action=payload.payload,
            )
            audit_service.log(
                event_type="approval_requested",
                event_status="pending",
                details_json={"approval_id": approval.id, "action_name": payload.action_name},
                task_id=task.id,
            )
            return ActionResponse(
                task_id=task.id,
                action_name=payload.action_name,
                result={
                    "status": "pending_approval",
                    "approval_id": approval.id,
                    "reason": guardrail["reason"],
                },
            )

        # ALLOWED - execute
        task_service.update_task_status(task, TaskStatus.PLANNING, current_step="planning action")
        task_service.update_task_status(task, TaskStatus.EXECUTING, current_step="executing action")

        result = action_service.run_action(
            action_name=payload.action_name,
            payload=payload.payload,
        )

        task_service.update_task_status(
            task, TaskStatus.COMPLETED, current_step="completed", result_json=result
        )
        audit_service.log(
            event_type="action_execution",
            event_status="completed",
            details_json=result,
            task_id=task.id,
        )

        return ActionResponse(
            task_id=task.id,
            action_name=payload.action_name,
            result=result,
        )

    except Exception as exc:
        task_service.update_task_status(
            task, TaskStatus.FAILED, current_step="failed", result_json={"error": str(exc)}
        )
        audit_service.log(
            event_type="action_execution",
            event_status="failed",
            details_json={"error": str(exc)},
            task_id=task.id,
        )
        return ActionResponse(
            task_id=task.id,
            action_name=payload.action_name,
            result={"status": "failed", "error": str(exc)},
        )
EOF

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
            "Task recognized. This request has been tracked for execution."
        )
        return state

    if state["route"] == "action":
        state["final_response"] = (
            "Action recognized. Use the /actions endpoint. "
            "Phase 3 enforces guardrails: actions may be allowed, blocked, or require approval."
        )
        return state

    memory_lines = state.get("context", {}).get("memory_snippets", [])
    memory_context = "\n".join(memory_lines) if memory_lines else "No memory context available."

    system_prompt = (
        "You are Jarvis Assistant Phase 3. "
        "Be concise, useful, structured, and execution-oriented. "
        "If asked to perform an action beyond current capabilities, say so clearly."
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
# Main app update
# -----------------------------------------------------------------------------

cat > apps/api/app/main.py << 'EOF'
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import actions, approvals, audit_logs, chat, memory, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME} in {settings.APP_ENV}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.3.0",
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
app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
app.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit_logs"])


@app.get("/")
def root():
    return {"status": "healthy", "app": settings.APP_NAME, "version": "0.3.0"}
EOF

# -----------------------------------------------------------------------------
# Frontend minimal update
# -----------------------------------------------------------------------------

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
          <div>Phase 3</div>
        </div>
      </div>
    </div>
  );
}
EOF

cat > apps/web/app/page.tsx << 'EOF'
"use client";

import { useCallback, useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import RightPanel from "@/components/RightPanel";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type ApprovalItem = {
  id: number;
  task_id: number;
  action_name: string;
  requested_action: Record<string, unknown>;
  status: string;
};

export default function HomePage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hello. I'm Jarvis Phase 3. Actions are now guarded: allowed, blocked, or requiring approval." },
  ]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [taskId, setTaskId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const loadApprovals = useCallback(async () => {
    try {
      const res = await fetch(`${apiBase}/approvals/`);
      const data: ApprovalItem[] = await res.json();
      setApprovals(data.filter((a) => a.status === "pending"));
    } catch { /* ignore */ }
  }, [apiBase]);

  useEffect(() => {
    loadApprovals();
  }, [loadApprovals]);

  const addMsg = (content: string) =>
    setMessages((prev) => [...prev, { role: "assistant", content }]);

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
        body: JSON.stringify({ content: trimmed, user_id: 1, conversation_id: conversationId }),
      });
      const data = await res.json();
      setConversationId(data.conversation_id ?? null);
      setTaskId(data.task_id ?? null);
      addMsg(data.response);
    } catch {
      addMsg("Something went wrong while contacting the backend.");
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
      addMsg(`Action: ${data.action_name} (Task #${data.task_id})\n${JSON.stringify(data.result, null, 2)}`);
      await loadApprovals();
    } catch {
      addMsg(`Action "${actionName}" failed.`);
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (approvalId: number, action: "approve" | "reject") => {
    try {
      await fetch(`${apiBase}/approvals/${approvalId}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision_notes: `${action}d from UI` }),
      });
      addMsg(`Approval #${approvalId} ${action}d.`);
      await loadApprovals();
    } catch {
      addMsg(`Failed to ${action} approval #${approvalId}.`);
    }
  };

  return (
    <div className="flex h-screen">
      <Sidebar />

      <main className="flex-1 flex flex-col bg-zinc-950">
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-2xl px-4 py-3 rounded-2xl whitespace-pre-wrap ${
                  msg.role === "user" ? "bg-blue-600" : "bg-zinc-800"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}

          {approvals.length > 0 && (
            <div className="space-y-3 pt-4 border-t border-zinc-800">
              <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide">
                Pending Approvals
              </h3>
              {approvals.map((a) => (
                <div key={a.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                  <div className="text-sm text-zinc-300 mb-2">
                    #{a.id} — <span className="font-medium text-white">{a.action_name}</span> (Task #{a.task_id})
                  </div>
                  <div className="text-xs text-zinc-500 mb-3 font-mono">
                    {JSON.stringify(a.requested_action)}
                  </div>
                  <div className="flex gap-2">
                    <button
                      className="rounded-lg bg-green-700 hover:bg-green-600 px-3 py-1.5 text-sm"
                      onClick={() => handleApproval(a.id, "approve")}
                    >
                      Approve
                    </button>
                    <button
                      className="rounded-lg bg-red-700 hover:bg-red-600 px-3 py-1.5 text-sm"
                      onClick={() => handleApproval(a.id, "reject")}
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-zinc-800 bg-zinc-900 p-4 space-y-3">
          <div className="flex gap-2">
            <input
              className="flex-1 rounded-2xl bg-zinc-800 border border-zinc-700 px-4 py-3 outline-none"
              type="text"
              value={input}
              placeholder="Ask Jarvis something..."
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") sendMessage(); }}
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
              onClick={() => runAction("create_file", { relative_path: "example/safe.txt", content: "Allowed write (safe prefix)" })}
              disabled={loading}
            >
              Safe File Write
            </button>
            <button
              className="rounded-xl bg-yellow-900 border border-yellow-700 px-4 py-2 text-sm hover:bg-yellow-800 disabled:opacity-50"
              onClick={() => runAction("create_file", { relative_path: "restricted/needs-approval.txt", content: "Requires approval" })}
              disabled={loading}
            >
              Approval-Required Write
            </button>
            <button
              className="rounded-xl bg-zinc-800 border border-zinc-700 px-4 py-2 text-sm hover:bg-zinc-700 disabled:opacity-50"
              onClick={() => runAction("http_request", { url: "https://httpbin.org/get" })}
              disabled={loading}
            >
              Allowed HTTP
            </button>
            <button
              className="rounded-xl bg-red-900 border border-red-700 px-4 py-2 text-sm hover:bg-red-800 disabled:opacity-50"
              onClick={() => runAction("http_request", { url: "https://google.com" })}
              disabled={loading}
            >
              Blocked HTTP
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

cat > docs/phase3-scope.md << 'EOF'
# Phase 3 Scope

Included:
- approval workflow (create/list/approve/reject)
- code-enforced guardrails (allow/block/approval_required)
- audit logging for all action lifecycle events
- MCP-ready tool abstraction layer
- approval-aware task lifecycle
- minimal frontend for approval management

Excluded:
- real MCP integration (Phase 4)
- OpenHands
- auth
- destructive GitHub execution
EOF

echo ""
echo "✅ Phase 3 files written."
echo ""
echo "Next:"
echo "1. docker compose down -v && docker compose up --build -d"
echo "2. in apps/web: npm run dev"
echo "3. test /actions, /approvals, /audit-logs"
echo ""
echo "Phase 3 bootstrap complete."
