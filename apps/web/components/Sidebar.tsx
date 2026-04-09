type Props = {
  pendingApprovals: number;
};

export default function Sidebar({ pendingApprovals }: Props) {
  return (
    <aside className="hidden w-72 border-r border-white/10 bg-slate-950/70 p-6 backdrop-blur-xl xl:block">
      <p className="eyebrow">Jarvis</p>
      <h2 className="mt-2 text-2xl font-semibold">Operator View</h2>
      <p className="mt-2 text-sm text-slate-300">
        Built for a solo operator: simple controls, approval safety, visible status.
      </p>

      <div className="mt-6 space-y-2 text-sm">
        <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">Chat and tasks</div>
        <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">Guided automation</div>
        <div className="rounded-xl border border-amber-300/50 bg-amber-300/10 px-4 py-3">
          Pending approvals: {pendingApprovals}
        </div>
      </div>

      <div className="mt-8 rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
        Tip: add your API key once in Connection Settings and it stays on this browser.
      </div>
    </aside>
  );
}
