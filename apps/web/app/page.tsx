"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import RightPanel from "@/components/RightPanel";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type Approval = {
  id: number;
  task_id: number;
  action_name: string;
  status: string;
};

export default function HomePage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hello. I'm Jarvis Phase 6. I can chat, run guarded actions, submit OpenHands execution requests, and handle GitHub workflow requests." }
  ]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [taskId, setTaskId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [executionMode, setExecutionMode] = useState<string>("local");
  const [mcpStatus, setMcpStatus] = useState<string>("unknown");

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const loadApprovals = async () => {
    try {
      const res = await fetch(`${apiBase}/approvals/`);
      const data = await res.json();
      setApprovals(data.filter((a: Approval) => a.status === "pending"));
    } catch { /* ignore */ }
  };

  const loadMcpStatus = async () => {
    try {
      const res = await fetch(`${apiBase}/mcp/status`);
      const data = await res.json();
      setMcpStatus(data.enabled ? `enabled (${data.default_mode})` : "disabled");
    } catch {
      setMcpStatus("unavailable");
    }
  };

  useEffect(() => {
    loadApprovals();
    loadMcpStatus();
  }, []);

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
        body: JSON.stringify({ content: trimmed, user_id: 1, conversation_id: conversationId })
      });

      const data = await res.json();
      setConversationId(data.conversation_id ?? null);
      setTaskId(data.task_id ?? null);
      setMessages((prev) => [...prev, { role: "assistant", content: data.response }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Something went wrong while contacting the backend." }]);
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
      setMessages((prev) => [...prev, { role: "assistant", content: `Action: ${data.action_name} (Task #${data.task_id})\nMode: ${mode ?? "n/a"}\n${JSON.stringify(data.result, null, 2)}` }]);
      await loadApprovals();
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: `Action "${actionName}" failed.` }]);
    } finally {
      setLoading(false);
    }
  };

  const runOpenHandsExecution = async (requestType: string, title: string, objective: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/execution/openhands`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: 1,
          conversation_id: conversationId,
          request_type: requestType,
          title,
          objective,
          context: { repo: "jarvis-ai-system" }
        })
      });

      const data = await res.json();
      setTaskId(data.task_id ?? null);
      setExecutionMode(data.execution_mode || "openhands_stub");
      setMessages((prev) => [...prev, { role: "assistant", content: `OpenHands [${requestType}]: Task #${data.task_id}\nMode: ${data.execution_mode}\n${JSON.stringify(data.result, null, 2)}` }]);
      await loadApprovals();
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "OpenHands execution failed." }]);
    } finally {
      setLoading(false);
    }
  };

  const runGitHubExecution = async (requestType: string, title: string, objective: string, context: Record<string, unknown> = {}) => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/execution/github/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: 1,
          conversation_id: conversationId,
          request_type: requestType,
          title,
          repo: "ismaelloveexcel/jarvis-ai-system",
          objective,
          context
        })
      });

      const data = await res.json();
      setTaskId(data.task_id ?? null);
      setExecutionMode(data.execution_mode || "github_readonly");
      setMessages((prev) => [...prev, { role: "assistant", content: `GitHub [${requestType}]: Task #${data.task_id}\nMode: ${data.execution_mode}\n${JSON.stringify(data.result, null, 2)}` }]);
      await loadApprovals();
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: `GitHub ${requestType} failed.` }]);
    } finally {
      setLoading(false);
    }
  };

  const approveItem = async (approvalId: number) => {
    try {
      await fetch(`${apiBase}/approvals/${approvalId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision_notes: "Approved from UI" })
      });
      await loadApprovals();
      setMessages((prev) => [...prev, { role: "assistant", content: `Approval #${approvalId} approved.` }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: `Failed to approve #${approvalId}.` }]);
    }
  };

  const rejectItem = async (approvalId: number) => {
    try {
      await fetch(`${apiBase}/approvals/${approvalId}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision_notes: "Rejected from UI" })
      });
      await loadApprovals();
      setMessages((prev) => [...prev, { role: "assistant", content: `Approval #${approvalId} rejected.` }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: `Failed to reject #${approvalId}.` }]);
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
          {messages.map((msg, index) => (
            <div key={index} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
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
                  <div className="flex gap-2">
                    <button className="rounded-lg bg-green-700 hover:bg-green-600 px-3 py-1.5 text-sm" onClick={() => approveItem(a.id)}>Approve</button>
                    <button className="rounded-lg bg-red-700 hover:bg-red-600 px-3 py-1.5 text-sm" onClick={() => rejectItem(a.id)}>Reject</button>
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
            <button className="rounded-xl bg-zinc-800 border border-zinc-700 px-4 py-2 text-sm hover:bg-zinc-700 disabled:opacity-50" onClick={() => runAction("create_file", { relative_path: "example/phase6.txt", content: "Hello from Phase 6!\n" + new Date().toISOString() })} disabled={loading}>Safe File Write</button>
            <button className="rounded-xl bg-yellow-900 border border-yellow-700 px-4 py-2 text-sm hover:bg-yellow-800 disabled:opacity-50" onClick={() => runAction("create_file", { relative_path: "restricted/p6.txt", content: "Requires approval" })} disabled={loading}>Approval Write</button>
            <button className="rounded-xl bg-zinc-800 border border-zinc-700 px-4 py-2 text-sm hover:bg-zinc-700 disabled:opacity-50" onClick={() => runAction("http_request", { url: "https://httpbin.org/get" })} disabled={loading}>Allowed HTTP</button>
            <button className="rounded-xl bg-red-900 border border-red-700 px-4 py-2 text-sm hover:bg-red-800 disabled:opacity-50" onClick={() => runAction("http_request", { url: "https://google.com" })} disabled={loading}>Blocked HTTP</button>
          </div>

          <div className="flex gap-2 flex-wrap border-t border-zinc-800 pt-3">
            <span className="text-xs text-zinc-500 self-center mr-2">OpenHands:</span>
            <button className="rounded-xl bg-purple-900 border border-purple-700 px-4 py-2 text-sm hover:bg-purple-800 disabled:opacity-50" onClick={() => runOpenHandsExecution("code_generation", "Generate feature module", "Prepare a plan and stub output for a new feature")} disabled={loading}>Code Gen</button>
            <button className="rounded-xl bg-purple-900 border border-purple-700 px-4 py-2 text-sm hover:bg-purple-800 disabled:opacity-50" onClick={() => runOpenHandsExecution("bug_fix_plan", "Bug fix analysis", "Analyze and plan a fix for a sample bug")} disabled={loading}>Bug Fix Plan</button>
          </div>

          <div className="flex gap-2 flex-wrap border-t border-zinc-800 pt-3">
            <span className="text-xs text-zinc-500 self-center mr-2">GitHub:</span>
            <button className="rounded-xl bg-emerald-900 border border-emerald-700 px-4 py-2 text-sm hover:bg-emerald-800 disabled:opacity-50" onClick={() => runGitHubExecution("repo_inspect", "Inspect repo", "Inspect repository structure", { inspection_scope: "root structure" })} disabled={loading}>Repo Inspect</button>
            <button className="rounded-xl bg-emerald-900 border border-emerald-700 px-4 py-2 text-sm hover:bg-emerald-800 disabled:opacity-50" onClick={() => runGitHubExecution("patch_proposal", "Patch proposal", "Draft a patch proposal for a new route", { branch_name: "feature/patch-proposal", pr_title: "Proposal: add new route" })} disabled={loading}>Patch Proposal</button>
            <button className="rounded-xl bg-emerald-900 border border-emerald-700 px-4 py-2 text-sm hover:bg-emerald-800 disabled:opacity-50" onClick={() => runGitHubExecution("pr_draft", "Draft PR", "Prepare a draft PR for review")} disabled={loading}>PR Draft</button>
            <button className="rounded-xl bg-yellow-900 border border-yellow-700 px-4 py-2 text-sm hover:bg-yellow-800 disabled:opacity-50" onClick={() => runGitHubExecution("repo_write_request", "Write request", "Prepare a write request for a feature branch", { target_branch: "main", proposed_branch: "feature/github-phase6", requested_changes: ["add workflow", "update docs"] })} disabled={loading}>Write Request (approval)</button>
          </div>
        </div>
      </main>

      <RightPanel taskId={taskId} conversationId={conversationId} executionMode={executionMode} />
    </div>
  );
}
