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

## Auth

Set `API_KEY` in `.env` to require `X-API-Key` header on all requests.
Leave blank to disable auth (dev mode).

```bash
# With auth enabled
curl -H "X-API-Key: your-key" http://localhost:8000/health
```

Root `/` and `/health` are always accessible regardless of auth.

## Migrations

```bash
cd apps/api

# Check current migration version
alembic current

# Apply pending migrations
alembic upgrade head

# Generate a new migration after model changes
alembic revision --autogenerate -m "description"
```

## Tests

```bash
cd apps/api
python -m pytest tests/ -v
```

## Key endpoints

| Prefix | Purpose |
|--------|---------|
| `GET /` | Health check (DB-aware, returns 503 if DB unavailable) |
| `GET /health` | Health check (machine-readable) |
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
- Rate limiting: configurable via `RATE_LIMIT` env var (default: 60/minute)

## Notes
- Live providers remain disabled — all external integrations run in stub mode
- No user auth / RBAC — API key auth only
- No background workers — `/execution/*`, `/execution/github/*`, and `/ops/request` queue work via FastAPI `BackgroundTasks` and return 202 (in-process async, not a separate worker queue)
- See `docs/v1-closeout.md` for full V1 scope and boundaries
