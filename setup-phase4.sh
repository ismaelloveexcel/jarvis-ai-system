#!/bin/bash
# =============================================================================
# Jarvis Assistant – Phase 4 Bootstrap Script
# Adds:
# - MCP config layer
# - MCP client/adapter layer
# - config-driven local vs MCP execution path
# - MCP audit logging
# - MCP status endpoints
#
# Assumes Phase 3 already exists in current repo root.
#
# FIXES vs original script:
# 1. Added __init__.py for mcp/providers/ (missing, causes import errors)
# 2. Appends MCP vars to .env (not just .env.example)
# 3. Frontend useEffect uses useCallback for stable references
# =============================================================================

set -euo pipefail

PROJECT_ROOT="."
cd "${PROJECT_ROOT}"

echo "🚀 Starting Jarvis Phase 4 bootstrap..."

mkdir -p apps/api/app/mcp/providers
mkdir -p apps/api/app/mcp/adapters

# -----------------------------------------------------------------------------
# .env.example + .env extension
# -----------------------------------------------------------------------------

for envfile in .env.example .env; do
  if [ -f "$envfile" ] && ! grep -q "^MCP_ENABLED=" "$envfile"; then
    cat >> "$envfile" << 'EOF'

# -----------------------------------------------------------------------------
# MCP
# -----------------------------------------------------------------------------
MCP_ENABLED=false
MCP_DEFAULT_MODE=local
MCP_FILESYSTEM_ENABLED=false
MCP_FETCH_ENABLED=false
MCP_GITHUB_READONLY_ENABLED=false
EOF
  fi
done

# -----------------------------------------------------------------------------
# Config update
# -----------------------------------------------------------------------------

cat > apps/api/app/core/config.py << 'EOF'
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "Jarvis Assistant"
    SECRET_KEY: str = "change-me"

    DATABASE_URL: str = "postgresql://jarvis:changeme123@postgres:5432/jarvis_db"

    LLM_PROVIDER: Literal["openai", "anthropic", "xai"] = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: str = ""

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    XAI_API_KEY: str = ""

    MCP_ENABLED: bool = False
    MCP_DEFAULT_MODE: Literal["local", "mcp"] = "local"
    MCP_FILESYSTEM_ENABLED: bool = False
    MCP_FETCH_ENABLED: bool = False
    MCP_GITHUB_READONLY_ENABLED: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
EOF

# -----------------------------------------------------------------------------
# MCP schemas
# -----------------------------------------------------------------------------

cat > apps/api/app/schemas/mcp.py << 'EOF'
from pydantic import BaseModel


class MCPStatusResponse(BaseModel):
    enabled: bool
    default_mode: str
    filesystem_enabled: bool
    fetch_enabled: bool
    github_readonly_enabled: bool


class MCPToolInfo(BaseModel):
    name: str
    enabled: bool
    mode: str
    description: str
EOF

# -----------------------------------------------------------------------------
# MCP base / init files / providers
# -----------------------------------------------------------------------------

cat > apps/api/app/mcp/__init__.py << 'EOF'
EOF

cat > apps/api/app/mcp/base.py << 'EOF'
class MCPExecutionError(Exception):
    pass


class MCPToolAdapter:
    """Base adapter interface for MCP tools.
    Phase 4 providers implement invoke() to either stub or
    call real MCP servers. Phase 5+ can swap in live implementations.
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name

    def invoke(self, payload: dict) -> dict:
        raise NotImplementedError

    def describe(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "parameters": {},
            "description": f"MCP tool: {self.tool_name}",
        }
EOF

cat > apps/api/app/mcp/providers/__init__.py << 'EOF'
EOF

cat > apps/api/app/mcp/adapters/__init__.py << 'EOF'
EOF

cat > apps/api/app/mcp/providers/filesystem_provider.py << 'EOF'
from app.mcp.base import MCPToolAdapter


class MCPFilesystemAdapter(MCPToolAdapter):
    def __init__(self):
        super().__init__("filesystem")

    def invoke(self, payload: dict) -> dict:
        return {
            "status": "success",
            "execution_mode": "mcp",
            "tool_name": self.tool_name,
            "note": "Filesystem MCP adapter invoked. Real MCP server integration available in Phase 5+.",
            "payload_received": payload,
        }
EOF

cat > apps/api/app/mcp/providers/fetch_provider.py << 'EOF'
from app.mcp.base import MCPToolAdapter


class MCPFetchAdapter(MCPToolAdapter):
    def __init__(self):
        super().__init__("fetch")

    def invoke(self, payload: dict) -> dict:
        return {
            "status": "success",
            "execution_mode": "mcp",
            "tool_name": self.tool_name,
            "note": "Fetch MCP adapter invoked. Real MCP server integration available in Phase 5+.",
            "payload_received": payload,
        }
EOF

cat > apps/api/app/mcp/providers/github_provider.py << 'EOF'
from app.mcp.base import MCPToolAdapter


class MCPGitHubReadOnlyAdapter(MCPToolAdapter):
    def __init__(self):
        super().__init__("github_readonly")

    def invoke(self, payload: dict) -> dict:
        return {
            "status": "success",
            "execution_mode": "mcp",
            "tool_name": self.tool_name,
            "note": "GitHub read-only MCP adapter invoked. Real MCP server integration available in Phase 5+.",
            "payload_received": payload,
        }
EOF

# -----------------------------------------------------------------------------
# MCP registry
# -----------------------------------------------------------------------------

cat > apps/api/app/mcp/registry.py << 'EOF'
from app.core.config import settings
from app.mcp.providers.filesystem_provider import MCPFilesystemAdapter
from app.mcp.providers.fetch_provider import MCPFetchAdapter
from app.mcp.providers.github_provider import MCPGitHubReadOnlyAdapter


class MCPRegistry:
    def __init__(self):
        self._tools: dict = {}

        if settings.MCP_FILESYSTEM_ENABLED:
            self._tools["filesystem"] = MCPFilesystemAdapter()

        if settings.MCP_FETCH_ENABLED:
            self._tools["fetch"] = MCPFetchAdapter()

        if settings.MCP_GITHUB_READONLY_ENABLED:
            self._tools["github_readonly"] = MCPGitHubReadOnlyAdapter()

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def get_tool(self, tool_name: str):
        return self._tools.get(tool_name)

    def list_tools(self) -> list[dict]:
        return [
            {"name": name, "enabled": True}
            for name in self._tools.keys()
        ]
EOF

# -----------------------------------------------------------------------------
# MCP service
# -----------------------------------------------------------------------------

cat > apps/api/app/services/mcp_service.py << 'EOF'
from app.core.config import settings
from app.mcp.registry import MCPRegistry


class MCPService:
    def __init__(self):
        self.registry = MCPRegistry()

    def get_status(self) -> dict:
        return {
            "enabled": settings.MCP_ENABLED,
            "default_mode": settings.MCP_DEFAULT_MODE,
            "filesystem_enabled": settings.MCP_FILESYSTEM_ENABLED,
            "fetch_enabled": settings.MCP_FETCH_ENABLED,
            "github_readonly_enabled": settings.MCP_GITHUB_READONLY_ENABLED,
        }

    def list_tools(self) -> list[dict]:
        tools = self.registry.list_tools()
        descriptions = {
            "filesystem": "MCP-backed filesystem capability",
            "fetch": "MCP-backed fetch/web retrieval capability",
            "github_readonly": "MCP-backed GitHub read-only capability",
        }
        return [
            {
                "name": tool["name"],
                "enabled": tool["enabled"],
                "mode": "mcp",
                "description": descriptions.get(tool["name"], "MCP tool"),
            }
            for tool in tools
        ]

    def execute(self, tool_name: str, payload: dict) -> dict:
        adapter = self.registry.get_tool(tool_name)
        if not adapter:
            raise ValueError(f"MCP tool '{tool_name}' is not enabled")
        return adapter.invoke(payload)
EOF

# -----------------------------------------------------------------------------
# Action service upgrade: local vs mcp routing
# -----------------------------------------------------------------------------

cat > apps/api/app/services/action_service.py << 'EOF'
from app.core.config import settings
from app.actions.action_registry import ActionRegistry
from app.services.mcp_service import MCPService

ACTION_TO_MCP_TOOL = {
    "create_file": "filesystem",
    "read_file": "filesystem",
    "http_request": "fetch",
    "github_repo_info_stub": "github_readonly",
}


class ActionService:
    def __init__(self):
        self.local_registry = ActionRegistry()
        self.mcp_service = MCPService()

    def resolve_execution_mode(self, action_name: str) -> str:
        if not settings.MCP_ENABLED:
            return "local"
        if settings.MCP_DEFAULT_MODE != "mcp":
            return "local"

        tool_name = ACTION_TO_MCP_TOOL.get(action_name)
        if not tool_name:
            return "local"

        if self.mcp_service.registry.has_tool(tool_name):
            return "mcp"

        return "local"

    def run_action(self, action_name: str, payload: dict) -> dict:
        mode = self.resolve_execution_mode(action_name)

        if mode == "mcp":
            tool_name = ACTION_TO_MCP_TOOL[action_name]
            result = self.mcp_service.execute(tool_name=tool_name, payload=payload)
            result["execution_mode"] = "mcp"
            result["action_name"] = action_name
            return result

        result = self.local_registry.execute(action_name=action_name, payload=payload)
        result["execution_mode"] = "local"
        return result

    def list_actions(self) -> list[dict]:
        return self.local_registry.list_actions()
EOF

# -----------------------------------------------------------------------------
# Actions router with MCP audit events
# (preserves Phase 3 guardrails + approvals)
# -----------------------------------------------------------------------------

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
        # Phase 3: Guardrail evaluation
        task_service.update_task_status(task, TaskStatus.ANALYZING, current_step="guardrail evaluation")
        guardrail = guardrail_service.evaluate(payload.action_name, payload.payload)

        # BLOCKED
        if guardrail["decision"] == "blocked":
            task_service.update_task_status(
                task, TaskStatus.FAILED, current_step="blocked",
                result_json={"status": "blocked", "reason": guardrail["reason"]},
            )
            audit_service.log(
                event_type="action_blocked", event_status="blocked",
                details_json={"action_name": payload.action_name, "reason": guardrail["reason"]},
                task_id=task.id,
            )
            return ActionResponse(task_id=task.id, action_name=payload.action_name,
                                  result={"status": "blocked", "reason": guardrail["reason"]})

        # APPROVAL REQUIRED
        if guardrail["decision"] == "approval_required":
            task_service.update_task_status(task, TaskStatus.WAITING_FOR_APPROVAL, current_step="waiting_for_approval")
            approval = approval_service.create_approval(
                task_id=task.id, action_name=payload.action_name, requested_action=payload.payload,
            )
            audit_service.log(
                event_type="approval_requested", event_status="pending",
                details_json={"approval_id": approval.id, "action_name": payload.action_name},
                task_id=task.id,
            )
            return ActionResponse(task_id=task.id, action_name=payload.action_name,
                                  result={"status": "pending_approval", "approval_id": approval.id, "reason": guardrail["reason"]})

        # ALLOWED - resolve execution mode and run
        task_service.update_task_status(task, TaskStatus.PLANNING, current_step="resolving execution mode")

        mode = action_service.resolve_execution_mode(payload.action_name)
        audit_service.log(
            event_type="mcp_requested" if mode == "mcp" else "action_requested",
            event_status="routing",
            details_json={"action_name": payload.action_name, "execution_mode": mode},
            task_id=task.id,
        )

        task_service.update_task_status(task, TaskStatus.EXECUTING, current_step=f"executing ({mode})")

        result = action_service.run_action(action_name=payload.action_name, payload=payload.payload)

        task_service.update_task_status(task, TaskStatus.COMPLETED, current_step="completed", result_json=result)

        audit_event = "mcp_completed" if result.get("execution_mode") == "mcp" else "action_execution"
        audit_service.log(
            event_type=audit_event, event_status="completed",
            details_json=result, task_id=task.id,
        )

        return ActionResponse(task_id=task.id, action_name=payload.action_name, result=result)

    except Exception as exc:
        task_service.update_task_status(
            task, TaskStatus.FAILED, current_step="failed", result_json={"error": str(exc)},
        )
        audit_service.log(
            event_type="mcp_failed", event_status="failed",
            details_json={"action_name": payload.action_name, "error": str(exc)},
            task_id=task.id,
        )
        return ActionResponse(task_id=task.id, action_name=payload.action_name,
                              result={"status": "failed", "error": str(exc)})
EOF

# -----------------------------------------------------------------------------
# MCP router
# -----------------------------------------------------------------------------

cat > apps/api/app/routers/mcp.py << 'EOF'
from fastapi import APIRouter
from app.schemas.mcp import MCPStatusResponse, MCPToolInfo
from app.services.mcp_service import MCPService

router = APIRouter()


@router.get("/status", response_model=MCPStatusResponse)
def get_mcp_status():
    status = MCPService().get_status()
    return MCPStatusResponse(**status)


@router.get("/tools", response_model=list[MCPToolInfo])
def list_mcp_tools():
    tools = MCPService().list_tools()
    return [MCPToolInfo(**tool) for tool in tools]
EOF

# -----------------------------------------------------------------------------
# Main app update
# -----------------------------------------------------------------------------

cat > apps/api/app/main.py << 'EOF'
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import actions, approvals, audit_logs, chat, mcp, memory, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME} in {settings.APP_ENV}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.4.0",
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
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])


@app.get("/")
def root():
    return {"status": "healthy", "app": settings.APP_NAME, "version": "0.4.0"}
EOF

# -----------------------------------------------------------------------------
# Frontend update
# -----------------------------------------------------------------------------

cat > apps/web/components/RightPanel.tsx << 'EOF'
type Props = {
  taskId: number | null;
  conversationId: number | null;
  executionMode?: string;
};

export default function RightPanel({ taskId, conversationId, executionMode }: Props) {
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
          <div>Phase 4</div>
        </div>
        <div className="bg-zinc-800 rounded-xl p-3">
          <div className="text-zinc-400">Execution Mode</div>
          <div>{executionMode ?? "—"}</div>
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
    { role: "assistant", content: "Hello. I'm Jarvis Phase 4. Actions route through local or MCP-backed execution based on config." },
  ]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [taskId, setTaskId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [executionMode, setExecutionMode] = useState<string>("—");
  const [mcpStatus, setMcpStatus] = useState<string>("loading...");

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const loadApprovals = useCallback(async () => {
    try {
      const res = await fetch(`${apiBase}/approvals/`);
      const data: ApprovalItem[] = await res.json();
      setApprovals(data.filter((a) => a.status === "pending"));
    } catch { /* ignore */ }
  }, [apiBase]);

  const loadMcpStatus = useCallback(async () => {
    try {
      const res = await fetch(`${apiBase}/mcp/status`);
      const data = await res.json();
      setMcpStatus(data.enabled ? `enabled (${data.default_mode})` : "disabled (local fallback)");
    } catch {
      setMcpStatus("unavailable");
    }
  }, [apiBase]);

  useEffect(() => {
    loadApprovals();
    loadMcpStatus();
  }, [loadApprovals, loadMcpStatus]);

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
        body: JSON.stringify({ user_id: 1, conversation_id: conversationId, action_name: actionName, payload }),
      });
      const data = await res.json();
      setTaskId(data.task_id ?? null);
      const mode = data.result?.execution_mode;
      if (mode) setExecutionMode(mode);
      addMsg(`Action: ${data.action_name} (Task #${data.task_id})\nMode: ${mode ?? "n/a"}\n${JSON.stringify(data.result, null, 2)}`);
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
        <div className="border-b border-zinc-800 px-6 py-3 text-sm text-zinc-400 flex gap-4">
          <span>MCP: {mcpStatus}</span>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-2xl px-4 py-3 rounded-2xl whitespace-pre-wrap ${msg.role === "user" ? "bg-blue-600" : "bg-zinc-800"}`}>
                {msg.content}
              </div>
            </div>
          ))}

          {approvals.length > 0 && (
            <div className="space-y-3 pt-4 border-t border-zinc-800">
              <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide">Pending Approvals</h3>
              {approvals.map((a) => (
                <div key={a.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                  <div className="text-sm text-zinc-300 mb-2">
                    #{a.id} — <span className="font-medium text-white">{a.action_name}</span> (Task #{a.task_id})
                  </div>
                  <div className="text-xs text-zinc-500 mb-3 font-mono">{JSON.stringify(a.requested_action)}</div>
                  <div className="flex gap-2">
                    <button className="rounded-lg bg-green-700 hover:bg-green-600 px-3 py-1.5 text-sm" onClick={() => handleApproval(a.id, "approve")}>Approve</button>
                    <button className="rounded-lg bg-red-700 hover:bg-red-600 px-3 py-1.5 text-sm" onClick={() => handleApproval(a.id, "reject")}>Reject</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-zinc-800 bg-zinc-900 p-4 space-y-3">
          <div className="flex gap-2">
            <input className="flex-1 rounded-2xl bg-zinc-800 border border-zinc-700 px-4 py-3 outline-none" type="text" value={input} placeholder="Ask Jarvis something..." onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") sendMessage(); }} />
            <button className="rounded-2xl bg-blue-600 px-6 py-3 font-medium disabled:opacity-50" onClick={sendMessage} disabled={loading}>{loading ? "..." : "Send"}</button>
          </div>

          <div className="flex gap-2 flex-wrap">
            <button className="rounded-xl bg-zinc-800 border border-zinc-700 px-4 py-2 text-sm hover:bg-zinc-700 disabled:opacity-50" onClick={() => runAction("create_file", { relative_path: "example/phase4.txt", content: "Hello from Phase 4!\n" + new Date().toISOString() })} disabled={loading}>Safe File Write</button>
            <button className="rounded-xl bg-yellow-900 border border-yellow-700 px-4 py-2 text-sm hover:bg-yellow-800 disabled:opacity-50" onClick={() => runAction("create_file", { relative_path: "restricted/p4.txt", content: "Requires approval" })} disabled={loading}>Approval Write</button>
            <button className="rounded-xl bg-zinc-800 border border-zinc-700 px-4 py-2 text-sm hover:bg-zinc-700 disabled:opacity-50" onClick={() => runAction("http_request", { url: "https://httpbin.org/get" })} disabled={loading}>Allowed HTTP</button>
            <button className="rounded-xl bg-red-900 border border-red-700 px-4 py-2 text-sm hover:bg-red-800 disabled:opacity-50" onClick={() => runAction("http_request", { url: "https://google.com" })} disabled={loading}>Blocked HTTP</button>
          </div>
        </div>
      </main>

      <RightPanel taskId={taskId} conversationId={conversationId} executionMode={executionMode} />
    </div>
  );
}
EOF

# -----------------------------------------------------------------------------
# Docs
# -----------------------------------------------------------------------------

cat > docs/phase4-scope.md << 'EOF'
# Phase 4 Scope

Included:
- MCP config layer (MCP_ENABLED, MCP_DEFAULT_MODE, per-provider flags)
- MCP adapters/providers (filesystem, fetch, github_readonly)
- config-driven local vs MCP execution routing
- MCP audit logging (mcp_requested, mcp_completed, mcp_failed)
- MCP status/tools endpoints
- execution_mode field in action results

Excluded:
- Real MCP server connections (Phase 5+)
- OpenHands
- auth
- destructive GitHub execution
EOF

echo ""
echo "✅ Phase 4 files written."
echo ""
echo "Phase 4 bootstrap complete."
