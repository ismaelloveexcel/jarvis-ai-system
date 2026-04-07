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
          <div>{conversationId ?? "\u2014"}</div>
        </div>
        <div className="bg-zinc-800 rounded-xl p-3">
          <div className="text-zinc-400">Task ID</div>
          <div>{taskId ?? "\u2014"}</div>
        </div>
        <div className="bg-zinc-800 rounded-xl p-3">
          <div className="text-zinc-400">Phase</div>
          <div>Phase 7</div>
        </div>
        <div className="bg-zinc-800 rounded-xl p-3">
          <div className="text-zinc-400">Execution Mode</div>
          <div>{executionMode ?? "\u2014"}</div>
        </div>
      </div>
    </div>
  );
}
