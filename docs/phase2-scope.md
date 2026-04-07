# Phase 2 Scope

Included:
- action engine with registry
- tool layer (filesystem, http, github stub)
- task execution routing (chat / task / action)
- create_file action (sandboxed to workspace/generated/)
- read_file action
- http_request action (GET only)
- github_repo_info_stub action
- task status lifecycle (created → analyzing → planning → executing → completed/failed)
- /actions/ API endpoint
- /actions/available endpoint
- minimal frontend action buttons

Excluded:
- MCP
- OpenHands
- approvals
- auth
- destructive GitHub execution
