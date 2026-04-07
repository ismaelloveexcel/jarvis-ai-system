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
