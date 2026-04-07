# Jarvis Assistant — V1

A multi-phase AI assistant system with FastAPI backend, Next.js frontend, and PostgreSQL.

## What V1 includes

| Phase | Layer |
|-------|-------|
| 1 | Chat UI, FastAPI, PostgreSQL, LangGraph routing, task/memory persistence |
| 2 | Action engine with registry, guardrails (allow/block/approval_required) |
| 3 | Approval workflow, audit logging |
| 4 | MCP config layer with stub providers |
| 5 | OpenHands execution integration (stub mode) |
| 6 | GitHub readonly execution workflow |
| 7 | Approval-gated GitHub mutations (branch, PR draft, patch) |
| 8 | Artifact generation (patch, diff preview, change bundle) |
| 9 | Live-safe GitHub mutation execution with repo allowlist |
| 10 | Ops/deployment layer with approval-gated deploy/promote/rollback |

## Run locally

### 1. Prepare env
```bash
cp .env.example .env
```
Edit `.env` and add your `LLM_API_KEY`.

### 2. Start backend + database
```bash
docker compose up --build
```

### 3. Start frontend
```bash
cd apps/web
npm install
npm run dev
```

### 4. Open
http://localhost:3000

## Key endpoints

| Prefix | Purpose |
|--------|---------|
| `POST /chat/message` | Conversational interface |
| `POST /actions/` | Action execution with guardrails |
| `GET /approvals/` | Pending approval queue |
| `GET /audit-logs/` | Full audit trail |
| `POST /execution/openhands` | OpenHands execution requests |
| `POST /execution/github/` | GitHub execution requests |
| `POST /execution/github/mutation/` | GitHub mutation requests |
| `POST /artifacts/generate` | Artifact generation |
| `POST /ops/request` | Ops/deployment requests |
| `GET /ops/runbooks` | Runbook listing |

## Safety model
- All deployment-like actions require human approval
- Merge is permanently blocked
- Stub mode is the default for all external integrations
- Full audit trail for every operation

## Notes
- No auth yet
- No autonomous deployment
- See `docs/v1-closeout.md` for full V1 scope and boundaries
