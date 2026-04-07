# Jarvis Assistant – Phase 5

## What this phase includes
- Next.js frontend
- FastAPI backend
- PostgreSQL
- LangGraph base flow
- Persistent tasks + memories
- Provider-agnostic model interface
- Action engine with guardrails and approvals
- MCP config layer with stub providers
- **OpenHands integration layer (stub mode)**
- **Execution request routing with task lifecycle**
- **Audit logging for all execution events**

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

## Phase 5 OpenHands endpoints
- `GET /execution/capabilities` — list supported request types and mode
- `POST /execution/openhands` — submit an execution request
- `GET /execution/status/{task_id}` — check execution task status

## Notes
- OpenHands runs in stub mode by default. Set `OPENHANDS_MODE=remote` for live runtime.
- No auth yet.
- No destructive GitHub actions.
- No autonomous deployment.
