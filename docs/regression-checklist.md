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
```
