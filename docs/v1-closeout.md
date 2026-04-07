# V1 Closeout

Tag: `v1-complete` (Phases 1–10)

## What works

| Layer | Capability | Mode |
|-------|-----------|------|
| Chat | Conversational interface with LLM routing | live (LiteLLM) |
| Actions | create_file, http_request, read_file with guardrails | live |
| Guardrails | allow / block / approval_required per action type | live |
| Approvals | Pending queue, approve/reject with task state + audit | live |
| Audit | Full event log for every domain (actions, execution, GitHub, mutation, artifacts, ops) | live |
| MCP | Config layer with stub providers (filesystem, fetch, GitHub readonly) | stub |
| OpenHands | Execution request routing with task lifecycle | stub |
| GitHub Execution | Readonly repo inspect, patch proposal, PR draft, write request | stub |
| GitHub Mutation | Approval-gated create_branch, create_patch_artifact, create_pr_draft, execute_repo_write | stub (live_safe available) |
| Artifacts | Patch generation, diff preview, change bundle, task-linked file storage | live (local filesystem) |
| Ops | Maintenance check, runbook lookup, deployment/promotion/rollback requests | stub (live_safe available) |
| Frontend | All 10 phases of buttons, approval UI, MCP status, right panel context | live |

## What is intentionally blocked

| Action | Reason |
|--------|--------|
| `merge_request` | Automatic merges are blocked by guardrail policy |
| Autonomous production deployment | All deployment-like ops require approval |
| Destructive repo mutations without approval | `execute_repo_write` is approval-gated |
| Auth bypass | No auth exists yet — intentional scope exclusion |
| Background workers | All execution is synchronous request/response |

## What still runs in stub mode

| Component | Stub behavior | What live would require |
|-----------|--------------|------------------------|
| MCP providers | Return capability metadata only | Real MCP server connections |
| OpenHands | Returns structured stub results | Running OpenHands runtime at `OPENHANDS_BASE_URL` |
| GitHub Execution | Returns simulated readonly results | Valid `GITHUB_TOKEN` + API calls |
| GitHub Mutation (default) | Returns simulated branch/PR results | `GITHUB_MUTATION_MODE=live`, valid token, repo in allowlist |
| Ops (default) | Returns simulated check/deploy results | `OPS_MODE=live_safe` + `OPS_ALLOW_LIVE_MAINTENANCE=true` |

## What would be Phase 11+ only

| Feature | Notes |
|---------|-------|
| Authentication / authorization | User identity, RBAC, token-based access |
| Real CI/CD integration | Trigger pipelines from ops requests |
| Monitoring / alerting integration | Connect to Grafana, PagerDuty, etc. |
| Background task execution | Async workers for long-running operations |
| Multi-tenant isolation | Per-org or per-team data separation |
| Live MCP server connections | Real filesystem, fetch, GitHub MCP providers |
| Webhook receivers | GitHub webhooks, deployment status callbacks |
| Audit log retention / export | Log rotation, S3 archival, compliance export |
| Rollback with state verification | Actual version tracking and pre/post checks |
| Environment configuration management | Real env configs beyond dev/staging/production labels |

## Operational boundaries

- All mutation and deployment actions are approval-gated
- No action can modify production without human approval
- Merge remains permanently blocked in V1
- Stub mode is the safe default for all external integrations
- Live-safe mode adds real API calls but keeps destructive operations blocked
- Audit trail covers every request, approval, execution, and failure
