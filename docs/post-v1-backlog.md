# Post-V1 Backlog

Items discovered during V1 closeout usage pass. None are blocking — all are quality-of-life improvements if the system grows beyond its current scale.

## Friction points (from V1 usage pass)

### 1. No cross-task linking
When a workflow spans multiple domains (artifact → mutation → ops deploy), each task is independent. There is no workflow_id or parent_task_id to correlate them. Audit review requires manual correlation by timestamp and user_id.

### 2. Approval queue has no filtering
`GET /approvals/` returns all approvals across all statuses and domains. At scale, this needs `?status=pending&domain=ops` or similar filtering. Fine at V1 volumes.

### 3. Stub results are static
Maintenance check always returns the same three "OK" checks regardless of actual system state. By design for V1, but anyone building on top of the ops layer should know the results are not real health data.

### 4. Orchestrator classifier is keyword-based
The LangGraph classifier in `apps/api/app/graph/orchestrator.py` uses substring matching against hardcoded keyword lists. Not a V1 issue since real interaction goes through specific endpoints, but becomes a problem if chat becomes the primary interface.

### 5. Duplicated guarded-execution pattern across routers
Each domain router (openhands, github, github_mutation, ops) repeats the same guardrail → create task → check decision → approval or execute → audit pattern. ~200 lines could be extracted into a shared helper, but adds coupling between domains. Leave unless a fourth+ domain is added.
