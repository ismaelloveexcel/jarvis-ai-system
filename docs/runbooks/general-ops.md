# General Ops Runbook

Standard operating procedures for the Jarvis AI system.

## Health Check

1. Verify API responds at `/` endpoint
2. Confirm database connectivity via `/chat/message`
3. Check MCP status at `/mcp/status`
4. Review recent audit logs at `/audit-logs/`

## Incident Response

1. Identify affected service (API, DB, frontend)
2. Check error logs in Docker: `docker compose logs jarvis-api`
3. Verify database health: `docker compose exec postgres pg_isready`
4. If API unresponsive, restart: `docker compose restart jarvis-api`
5. Escalate if not resolved within 15 minutes

## Rollback Procedure

1. Identify the last known good version/tag
2. Submit rollback request via `/ops/request` with type `rollback_request`
3. Await approval from operations lead
4. Verify rollback completed successfully
5. Run regression checklist
