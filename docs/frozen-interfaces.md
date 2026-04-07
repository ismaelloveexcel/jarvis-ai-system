# Frozen Interfaces

These API contracts are stable as of Phase 7 (tag phase7-stable).
Do NOT change request/response shapes without a migration plan.

## Endpoints

### Actions (Phase 2)
- `GET  /actions/available` — list registered actions
- `POST /actions/` — execute an action through guardrails

### Approvals (Phase 3)
- `GET  /approvals/` — list all approvals
- `POST /approvals/{id}/approve` — approve a pending item
- `POST /approvals/{id}/reject` — reject a pending item

### Audit Logs (Phase 3)
- `GET  /audit-logs/` — list all audit log entries

### MCP (Phase 4)
- `GET  /mcp/status` — MCP feature flag state
- `GET  /mcp/tools` — list enabled MCP tools

### Execution (Phase 5)
- `GET  /execution/capabilities` — OpenHands config and supported request types
- `POST /execution/openhands` — submit an execution request
- `GET  /execution/status/{task_id}` — check execution task status

### GitHub Execution (Phase 6)
- `GET  /execution/github/capabilities` — GitHub execution config and supported request types
- `POST /execution/github/` — submit a GitHub execution request
- `GET  /execution/github/status/{task_id}` — check GitHub execution task status

### GitHub Mutation (Phase 7)
- `GET  /execution/github/mutation/capabilities` — mutation config and supported request types
- `POST /execution/github/mutation/` — submit a mutation request (approval-gated)
- `GET  /execution/github/mutation/status/{task_id}` — check mutation task status

### Core (Phase 1)
- `GET  /` — health check
- `POST /chat/message` — send a chat message
- `GET  /tasks/` — list tasks
- `GET  /tasks/{id}` — get task detail
- `GET  /memory/` — list memories
- `POST /memory/` — create a memory

## Request/Response Contracts

### POST /actions/
```json
// Request
{"action_name": "string", "payload": {}}
// Response
{"task_id": 0, "action_name": "string", "result": {}}
```

### POST /execution/openhands
```json
// Request
{"user_id": 1, "conversation_id": null, "request_type": "code_generation|repo_scaffold|file_refactor|bug_fix_plan", "title": "string", "objective": "string", "context": {}}
// Response
{"task_id": 0, "execution_mode": "string", "result": {}}
```

### POST /approvals/{id}/approve or /reject
```json
// Request
{"decision_notes": "string|null"}
// Response
{"id": 0, "task_id": 0, "action_name": "string", "requested_action": {}, "status": "string", "decision_notes": "string|null"}
```

### POST /execution/github/mutation/
```json
// Request
{"user_id": 1, "conversation_id": null, "request_type": "create_branch|create_patch_artifact|create_pr_draft|execute_repo_write|merge_request", "title": "string", "repo": "string|null", "objective": "string", "context": {}}
// Response
{"task_id": 0, "execution_mode": "string", "result": {}}
```

## Rules
- New endpoints may be added. Existing endpoints must not change shape.
- New fields may be added to responses. Existing fields must not be removed or renamed.
- New optional fields may be added to requests. Existing required fields must not change.
