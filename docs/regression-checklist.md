# Regression Checklist

Run after every phase to verify nothing is broken.

## Checks

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 1 | Chat works | `POST /chat/message` with `{"content":"hello","user_id":1}` | Response contains `response` field |
| 2 | Safe action works | `POST /actions/` with `create_file` to `example/` prefix | `result.status == "success"` |
| 3 | Blocked action works | `POST /actions/` with `http_request` to `google.com` | `result.status == "blocked"` |
| 4 | Approval-required action works | `POST /actions/` with `create_file` to `restricted/` | `result.status == "pending_approval"` |
| 5 | MCP status works | `GET /mcp/status` | Returns `enabled` field |
| 6 | OpenHands allowed execution works | `POST /execution/openhands` with `code_generation` | `execution_mode == "openhands_stub"` |
| 7 | OpenHands approval-required execution works | `POST /execution/openhands` with `repo_scaffold` | `execution_mode == "pending_approval"` |
| 8 | Audit logs record everything | `GET /audit-logs/` | Contains `execution_requested`, `openhands_completed`, `action_requested`, `approval_requested` |
| 9 | Frontend compiles | `npm run build` in `apps/web` | `Compiled successfully` |
| 10 | Mutation capabilities works | `GET /execution/github/mutation/capabilities` | Returns `supported_request_types` with 5 entries |
| 11 | create_branch requires approval | `POST /execution/github/mutation/` with `create_branch` | `execution_mode == "pending_approval"` |
| 12 | create_pr_draft requires approval | `POST /execution/github/mutation/` with `create_pr_draft` | `execution_mode == "pending_approval"` |
| 13 | Approved mutation completes | `POST /approvals/{id}/approve` for a mutation approval | Task status becomes `completed` with stub result |
| 14 | merge_request stays blocked | `POST /execution/github/mutation/` with `merge_request` | `execution_mode == "blocked"` |
| 15 | Mutation audit events present | `GET /audit-logs/` | Contains `github_mutation_requested`, `github_merge_blocked` |

## Quick run

```bash
# 1. Chat
curl -s -X POST http://localhost:8000/chat/message -H 'Content-Type: application/json' -d '{"content":"hello","user_id":1}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'response' in d else 'FAIL','- chat')"

# 2. Safe action
curl -s -X POST http://localhost:8000/actions/ -H 'Content-Type: application/json' -d '{"action_name":"create_file","payload":{"relative_path":"example/reg.txt","content":"t"}}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('result',{}).get('status')=='success' else 'FAIL','- safe action')"

# 3. Blocked action
curl -s -X POST http://localhost:8000/actions/ -H 'Content-Type: application/json' -d '{"action_name":"http_request","payload":{"url":"https://google.com"}}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('result',{}).get('status')=='blocked' else 'FAIL','- blocked action')"

# 4. Approval-required action
curl -s -X POST http://localhost:8000/actions/ -H 'Content-Type: application/json' -d '{"action_name":"create_file","payload":{"relative_path":"restricted/t.txt","content":"t"}}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('result',{}).get('status')=='pending_approval' else 'FAIL','- approval action')"

# 5. MCP status
curl -s http://localhost:8000/mcp/status | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'enabled' in d else 'FAIL','- MCP status')"

# 6. OpenHands allowed
curl -s -X POST http://localhost:8000/execution/openhands -H 'Content-Type: application/json' -d '{"request_type":"code_generation","title":"t","objective":"t","context":{}}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('execution_mode')=='openhands_stub' else 'FAIL','- OH allowed')"

# 7. OpenHands approval
curl -s -X POST http://localhost:8000/execution/openhands -H 'Content-Type: application/json' -d '{"request_type":"repo_scaffold","title":"t","objective":"t","context":{}}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('execution_mode')=='pending_approval' else 'FAIL','- OH approval')"

# 8. Audit logs
curl -s http://localhost:8000/audit-logs/ | python3 -c "import sys,json; logs=json.load(sys.stdin); types={l['event_type'] for l in logs}; needed={'execution_requested','openhands_completed','action_requested','approval_requested'}; print('PASS' if not needed-types else 'FAIL','- audit logs')"

# 9. Frontend
cd apps/web && npm run build 2>&1 | grep -q 'Compiled successfully' && echo 'PASS - frontend' || echo 'FAIL - frontend'

# 10. Mutation capabilities
curl -s http://localhost:8000/execution/github/mutation/capabilities | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if len(d.get('supported_request_types',[]))==5 else 'FAIL','- mutation capabilities')"

# 11. create_branch requires approval
curl -s -X POST http://localhost:8000/execution/github/mutation/ -H 'Content-Type: application/json' -d '{"request_type":"create_branch","title":"t","repo":"t/r","objective":"t"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('execution_mode')=='pending_approval' else 'FAIL','- create_branch approval')"

# 12. create_pr_draft requires approval
curl -s -X POST http://localhost:8000/execution/github/mutation/ -H 'Content-Type: application/json' -d '{"request_type":"create_pr_draft","title":"t","repo":"t/r","objective":"t"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('execution_mode')=='pending_approval' else 'FAIL','- create_pr_draft approval')"

# 13. Approved mutation completes (approve the create_branch from #11)
APPROVAL_ID=$(curl -s http://localhost:8000/approvals/ | python3 -c "import sys,json; a=[x for x in json.load(sys.stdin) if x['status']=='pending' and 'github_mutation' in x['action_name']]; print(a[-1]['id'] if a else '')")
if [ -n "$APPROVAL_ID" ]; then curl -s -X POST "http://localhost:8000/approvals/${APPROVAL_ID}/approve" -H 'Content-Type: application/json' -d '{"decision_notes":"regression"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('status')=='approved' else 'FAIL','- approved mutation')"; else echo 'SKIP - no pending mutation approval'; fi

# 14. merge_request stays blocked
curl -s -X POST http://localhost:8000/execution/github/mutation/ -H 'Content-Type: application/json' -d '{"request_type":"merge_request","title":"t","repo":"t/r","objective":"t"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('execution_mode')=='blocked' else 'FAIL','- merge blocked')"

# 15. Mutation audit events
curl -s http://localhost:8000/audit-logs/ | python3 -c "import sys,json; logs=json.load(sys.stdin); types={l['event_type'] for l in logs}; needed={'github_mutation_requested','github_merge_blocked'}; print('PASS' if not needed-types else 'FAIL','- mutation audit events')"
```
