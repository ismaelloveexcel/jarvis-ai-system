# Phase 4 Scope

Included:
- MCP config layer (MCP_ENABLED, MCP_DEFAULT_MODE, per-provider flags)
- MCP adapters/providers (filesystem, fetch, github_readonly)
- config-driven local vs MCP execution routing
- MCP audit logging (mcp_requested, mcp_completed, mcp_failed)
- MCP status/tools endpoints
- execution_mode field in action results

Excluded:
- Real MCP server connections (Phase 5+)
- OpenHands
- auth
- destructive GitHub execution
