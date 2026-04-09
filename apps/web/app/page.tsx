"use client";

import { useEffect, useMemo, useState } from "react";
import Sidebar from "@/components/Sidebar";
import RightPanel from "@/components/RightPanel";
import ApprovalDetail from "@/components/ApprovalDetail";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type Approval = {
  id: number;
  task_id: number;
  action_name: string;
  requested_action: Record<string, unknown>;
  status: string;
  decision_notes?: string;
  expires_at?: string;
  approved_by?: number;
  approved_at?: string;
};

type ActionCard = {
  title: string;
  description: string;
  buttonLabel: string;
  onRun: () => Promise<void>;
};

export default function HomePage() {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Welcome. Describe what you want done and I will run the safest path first, then ask for approval when needed.",
    },
  ]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [taskId, setTaskId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [selectedApproval, setSelectedApproval] = useState<Approval | null>(null);
  const [executionMode, setExecutionMode] = useState("idle");
  const [mcpStatus, setMcpStatus] = useState("checking");
  const [healthStatus, setHealthStatus] = useState("checking");
  const [apiKey, setApiKey] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [apiProtected, setApiProtected] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem("jarvis_api_key") || "";
    setApiKey(stored);
  }, []);

  useEffect(() => {
    window.localStorage.setItem("jarvis_api_key", apiKey);
  }, [apiKey]);

  const request = async (path: string, init: RequestInit = {}) => {
    const headers = new Headers(init.headers || {});
    if (init.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    if (apiKey.trim()) {
      headers.set("X-API-Key", apiKey.trim());
    }

    const response = await fetch(`${apiBase}${path}`, { ...init, headers });
    const text = await response.text();
    let data: unknown = {};
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text };
      }
    }

    if (response.status === 401) {
      setApiProtected(true);
      throw new Error("API key missing or invalid. Add it in Connection Settings.");
    }

    if (!response.ok) {
      const detail = typeof data === "object" && data && "detail" in data ? String((data as { detail: unknown }).detail) : `Request failed (${response.status})`;
      throw new Error(detail);
    }

    return data;
  };

  const addAssistantMessage = (content: string) => {
    setMessages((prev) => [...prev, { role: "assistant", content }]);
  };

  const loadApprovals = async () => {
    try {
      const data = await request("/approvals/");
      const pending = Array.isArray(data) ? (data as Approval[]) : [];
      setApprovals(pending.filter((approval) => approval.status === "pending"));
      setApiProtected(false);
    } catch (error) {
      setApprovals([]);
      if (error instanceof Error) {
        addAssistantMessage(error.message);
      }
    }
  };

  const loadMcpStatus = async () => {
    try {
      const data = (await request("/mcp/status")) as Record<string, unknown>;
      const enabled = Boolean(data.enabled);
      const mode = String(data.default_mode || "local");
      setMcpStatus(enabled ? `enabled (${mode})` : "disabled");
    } catch {
      setMcpStatus("unavailable");
    }
  };

  const loadHealth = async () => {
    try {
      const response = await fetch(`${apiBase}/health`);
      const data = await response.json();
      setHealthStatus(String(data.status || "unknown"));
    } catch {
      setHealthStatus("unreachable");
    }
  };

  useEffect(() => {
    loadHealth();
    loadMcpStatus();
    loadApprovals();

    const refreshInterval = window.setInterval(() => {
      loadHealth();
      loadApprovals();
    }, 15000);

    return () => window.clearInterval(refreshInterval);
  }, []);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    setLoading(true);

    try {
      const data = (await request("/chat/message", {
        method: "POST",
        body: JSON.stringify({ content: trimmed, user_id: 1, conversation_id: conversationId }),
      })) as Record<string, unknown>;

      setConversationId((data.conversation_id as number) ?? null);
      setTaskId((data.task_id as number) ?? null);
      addAssistantMessage(String(data.response || "No response from backend."));
    } catch (error) {
      if (error instanceof Error) {
        addAssistantMessage(error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const runAction = async (actionName: string, payload: Record<string, unknown>) => {
    setLoading(true);
    try {
      const data = (await request("/actions/", {
        method: "POST",
        body: JSON.stringify({ user_id: 1, conversation_id: conversationId, action_name: actionName, payload }),
      })) as Record<string, unknown>;

      setTaskId((data.task_id as number) ?? null);
      const result = (data.result || {}) as Record<string, unknown>;
      const mode = String(result.execution_mode || "action");
      setExecutionMode(mode);
      addAssistantMessage(`Action complete: ${String(data.action_name || actionName)}\nMode: ${mode}`);
      await loadApprovals();
    } catch (error) {
      if (error instanceof Error) {
        addAssistantMessage(error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const runExecution = async () => {
    setLoading(true);
    try {
      const data = (await request("/execution/openhands", {
        method: "POST",
        body: JSON.stringify({
          user_id: 1,
          conversation_id: conversationId,
          request_type: "code_generation",
          title: "Draft implementation plan",
          objective: "Create an implementation plan for the latest user instruction",
          context: { repo: "jarvis-ai-system" },
        }),
      })) as Record<string, unknown>;

      setTaskId((data.task_id as number) ?? null);
      setExecutionMode(String(data.execution_mode || "async"));
      addAssistantMessage(`Execution started as task #${String(data.task_id || "-")}. I will keep progress in the right panel.`);
      await loadApprovals();
    } catch (error) {
      if (error instanceof Error) {
        addAssistantMessage(error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const runOpsCheck = async () => {
    setLoading(true);
    try {
      const data = (await request("/ops/request", {
        method: "POST",
        body: JSON.stringify({
          user_id: 1,
          conversation_id: conversationId,
          request_type: "maintenance_check",
          title: "Maintenance check",
          environment: "dev",
          context: {},
        }),
      })) as Record<string, unknown>;
      setTaskId((data.task_id as number) ?? null);
      setExecutionMode(String(data.execution_mode || "ops"));
      addAssistantMessage(`Maintenance check requested as task #${String(data.task_id || "-")}.`);
      await loadApprovals();
    } catch (error) {
      if (error instanceof Error) {
        addAssistantMessage(error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const runSafeWrite = async () => {
    await runAction("create_file", {
      relative_path: "example/quick-note.txt",
      content: `Created from dashboard at ${new Date().toISOString()}\n`,
    });
  };

  const runRestrictedWrite = async () => {
    await runAction("create_file", {
      relative_path: "restricted/requires-approval.txt",
      content: "This operation should request approval.",
    });
  };

  const approveItem = async (approval: Approval, notes: string) => {
    try {
      await request(`/approvals/${approval.id}/approve`, {
        method: "POST",
        body: JSON.stringify({ decision_notes: notes || "Approved from dashboard" }),
      });
      await loadApprovals();
      setSelectedApproval(null);
      addAssistantMessage(`Approval #${approval.id} approved.`);
    } catch (error) {
      if (error instanceof Error) {
        addAssistantMessage(error.message);
      }
    }
  };

  const rejectItem = async (approvalId: number, notes: string) => {
    try {
      await request(`/approvals/${approvalId}/reject`, {
        method: "POST",
        body: JSON.stringify({ decision_notes: notes || "Rejected from dashboard" }),
      });
      await loadApprovals();
      setSelectedApproval(null);
      addAssistantMessage(`Approval #${approvalId} rejected.`);
    } catch (error) {
      if (error instanceof Error) {
        addAssistantMessage(error.message);
      }
    }
  };

  const actionCards: ActionCard[] = useMemo(
    () => [
      {
        title: "Create a safe note",
        description: "Writes a file in the safe workspace area.",
        buttonLabel: "Run safe write",
        onRun: runSafeWrite,
      },
      {
        title: "Try an approval flow",
        description: "Creates a restricted write so you can approve or reject it.",
        buttonLabel: "Start approval demo",
        onRun: runRestrictedWrite,
      },
      {
        title: "Generate a coding plan",
        description: "Runs OpenHands-style planning as an async task.",
        buttonLabel: "Start execution",
        onRun: runExecution,
      },
      {
        title: "Run maintenance check",
        description: "Checks operational readiness and returns a status report.",
        buttonLabel: "Run ops check",
        onRun: runOpsCheck,
      },
    ],
    []
  );

  return (
    <div className="min-h-screen bg-app-bg text-slate-100">
      <div className="absolute inset-0 -z-10 bg-app-glow" />
      <div className="flex min-h-screen">
        <Sidebar pendingApprovals={approvals.length} />

        <main className="flex-1 px-4 py-6 md:px-8">
          <section className="panel mb-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="eyebrow">Solo Assistant Console</p>
                <h1 className="hero-title">Run work safely without command-line overhead</h1>
                <p className="hero-subtitle">
                  Describe the result you want. Jarvis chooses the safest route, asks for approval when needed, and keeps task progress visible.
                </p>
              </div>
              <button
                type="button"
                className="pill-button"
                onClick={() => setShowSettings((value) => !value)}
              >
                {showSettings ? "Hide Connection Settings" : "Show Connection Settings"}
              </button>
            </div>

            {showSettings && (
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <div>
                  <label className="input-label" htmlFor="api-base">API Base URL</label>
                  <input
                    id="api-base"
                    className="input-box"
                    value={apiBase}
                    readOnly
                  />
                </div>
                <div>
                  <label className="input-label" htmlFor="api-key">API Key</label>
                  <input
                    id="api-key"
                    className="input-box"
                    value={apiKey}
                    onChange={(event) => setApiKey(event.target.value)}
                    placeholder="Paste X-API-Key here"
                  />
                </div>
              </div>
            )}

            <div className="mt-4 flex flex-wrap gap-2">
              <span className="status-chip">API: {healthStatus}</span>
              <span className="status-chip">MCP: {mcpStatus}</span>
              <span className="status-chip">Mode: {executionMode}</span>
              <span className="status-chip">Pending approvals: {approvals.length}</span>
              {apiProtected && <span className="status-chip status-warning">Protected API key required</span>}
            </div>
          </section>

          <section className="grid gap-5 lg:grid-cols-2">
            <div className="panel space-y-4">
              <h2 className="section-title">Ask Jarvis</h2>
              <div className="chat-log">
                {messages.map((message, index) => (
                  <div key={index} className={`chat-row ${message.role === "user" ? "chat-user" : "chat-assistant"}`}>
                    <div className="chat-bubble">{message.content}</div>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  className="input-box flex-1"
                  type="text"
                  value={input}
                  placeholder="Example: summarize today's system status and suggest next safe action"
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      void sendMessage();
                    }
                  }}
                />
                <button className="cta-button" onClick={() => void sendMessage()} disabled={loading}>
                  {loading ? "Working..." : "Send"}
                </button>
              </div>
            </div>

            <div className="panel space-y-4">
              <h2 className="section-title">Guided Actions</h2>
              <div className="space-y-3">
                {actionCards.map((card) => (
                  <div key={card.title} className="action-card">
                    <div>
                      <h3 className="font-semibold">{card.title}</h3>
                      <p className="text-sm text-slate-300">{card.description}</p>
                    </div>
                    <button className="pill-button" disabled={loading} onClick={() => void card.onRun()}>
                      {card.buttonLabel}
                    </button>
                  </div>
                ))}
              </div>

              {approvals.length > 0 && (
                <div className="mt-2 border-t border-white/10 pt-3">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-amber-200">Pending approvals</h3>
                  <div className="mt-2 space-y-2">
                    {approvals.map((approval) => (
                      <button
                        key={approval.id}
                        type="button"
                        className="w-full rounded-xl border border-white/10 bg-white/5 p-3 text-left transition hover:border-amber-300/70 hover:bg-white/10"
                        onClick={() => setSelectedApproval(approval)}
                      >
                        <div className="text-sm">#{approval.id} - {approval.action_name}</div>
                        <div className="text-xs text-slate-300">Task #{approval.task_id}. Click to review and decide.</div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>
        </main>

        <RightPanel
          taskId={taskId}
          conversationId={conversationId}
          executionMode={executionMode}
          healthStatus={healthStatus}
          pendingApprovals={approvals.length}
        />
      </div>

      {selectedApproval && (
        <ApprovalDetail
          approval={selectedApproval}
          apiBase={apiBase}
          apiKey={apiKey}
          onClose={() => setSelectedApproval(null)}
          onApprove={approveItem}
          onReject={rejectItem}
        />
      )}
    </div>
  );
}
