type Props = {
  taskId: number | null;
  conversationId: number | null;
  executionMode?: string;
  healthStatus: string;
  pendingApprovals: number;
};

export default function RightPanel({
  taskId,
  conversationId,
  executionMode,
  healthStatus,
  pendingApprovals,
}: Props) {
  return (
    <aside className="hidden w-80 border-l border-white/10 bg-slate-950/70 p-5 backdrop-blur-xl lg:block">
      <h2 className="text-lg font-semibold mb-4">Live Snapshot</h2>
      <div className="space-y-3 text-sm text-slate-200">
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <div className="text-slate-300">API health</div>
          <div className="font-semibold">{healthStatus}</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <div className="text-slate-300">Conversation</div>
          <div>{conversationId ?? "-"}</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <div className="text-slate-300">Most recent task</div>
          <div>{taskId ?? "-"}</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <div className="text-slate-300">Execution mode</div>
          <div>{executionMode ?? "-"}</div>
        </div>
        <div className="rounded-xl border border-amber-300/40 bg-amber-300/10 p-3">
          <div className="text-amber-100">Approvals waiting</div>
          <div className="text-xl font-semibold">{pendingApprovals}</div>
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-white/10 bg-white/5 p-3 text-xs text-slate-300">
        Tasks run asynchronously. For sensitive actions, approvals appear in the center panel.
      </div>
    </aside>
  );
}
