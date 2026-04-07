# Regression Checklist

Run after every change to verify nothing is broken.

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
| 8 | Audit logs record everything | `GET /audit-logs/` | Contains expected event types |
| 9 | Frontend compiles | `npm run build` in `apps/web` | Exit code 0 |
| 10 | Mutation capabilities works | `GET /execution/github/mutation/capabilities` | Returns `supported_request_types` with 5 entries |
| 11 | create_branch requires approval | `POST /execution/github/mutation/` with `create_branch` | `execution_mode == "pending_approval"` |
| 12 | create_pr_draft requires approval | `POST /execution/github/mutation/` with `create_pr_draft` | `execution_mode == "pending_approval"` |
| 13 | Approved mutation completes | `POST /approvals/{id}/approve` for a mutation approval | Task status becomes `completed` with stub result |
| 14 | merge_request stays blocked | `POST /execution/github/mutation/` with `merge_request` | `execution_mode == "blocked"` |
| 15 | Mutation audit events present | `GET /audit-logs/` | Contains `github_mutation_requested`, `github_merge_blocked` |
| 16 | Artifact capabilities works | `GET /artifacts/capabilities` | Returns `supported_request_types` with 4 entries |
| 17 | Patch artifact generation works | `POST /artifacts/generate` with `generate_patch_artifact` | `result.status == "success"`, `artifact_id` present |
| 18 | Diff preview generation works | `POST /artifacts/generate` with `generate_diff_preview` | `result.status == "success"`, `artifact_id` present |
| 19 | Task artifact listing works | `GET /artifacts/task/{task_id}` | Returns array with artifact linked to task |
| 20 | Artifact file retrieval works | `GET /artifacts/file/{artifact_id}` | Returns artifact file content as plain text |
| 21 | Artifact audit events present | `GET /audit-logs/` | Contains `artifact_requested`, `artifact_generated` |
| 22 | Mutation live-status works | `GET /execution/github/mutation/live-status` | Returns `mode` field |
| 23 | Ops capabilities works | `GET /ops/capabilities` | Returns `supported_request_types` with 5 entries |
| 24 | Ops status works | `GET /ops/status` | Returns `ops_enabled` and `ops_mode` fields |
| 25 | Maintenance check runs immediately | `POST /ops/request` with `maintenance_check` | `execution_mode == "ops_stub"`, `result.status == "success"` |
| 26 | Deployment request requires approval | `POST /ops/request` with `deployment_request` | `execution_mode == "pending_approval"` |
| 27 | Rollback request requires approval | `POST /ops/request` with `rollback_request` | `execution_mode == "pending_approval"` |
| 28 | Approved ops request completes | `POST /approvals/{id}/approve` for an ops approval | Task status becomes `completed` with stub result |
| 29 | Ops runbooks works | `GET /ops/runbooks` | Returns array with runbook entries |
| 30 | Ops audit events present | `GET /audit-logs/` | Contains `ops_requested`, `ops_completed` |

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
curl -s http://localhost:8000/audit-logs/ | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if len(d)>0 else 'FAIL','- audit logs')"

# 9. Frontend
cd apps/web && npm run build 2>&1 | tail -1 | grep -q 'Static' && echo 'PASS - frontend' || echo 'FAIL - frontend'; cd ../..

# 10. Mutation capabilities
curl -s http://localhost:8000/execution/github/mutation/capabilities | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if len(d.get('supported_request_types',[]))==5 else 'FAIL','- mutation capabilities')"

# 11. create_branch requires approval
curl -s -X POST http://localhost:8000/execution/github/mutation/ -H 'Content-Type: application/json' -d '{"request_type":"create_branch","title":"t","repo":"t/r","objective":"t"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('execution_mode')=='pending_approval' else 'FAIL','- create_branch approval')"

# 12. create_pr_draft requires approval
curl -s -X POST http://localhost:8000/execution/github/mutation/ -H 'Content-Type: application/json' -d '{"request_type":"create_pr_draft","title":"t","repo":"t/r","objective":"t"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('execution_mode')=='pending_approval' else 'FAIL','- create_pr_draft approval')"

# 13. Approved mutation completes
APPROVAL_ID=$(curl -s http://localhost:8000/approvals/ | python3 -c "import sys,json; a=[x for x in json.load(sys.stdin) if x['status']=='pending' and 'github_mutation' in x['action_name']]; print(a[-1]['id'] if a else '')")
if [ -n "$APPROVAL_ID" ]; then curl -s -X POST "http://localhost:8000/approvals/${APPROVAL_ID}/approve" -H 'Content-Type: application/json' -d '{"decision_notes":"regression"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('status')=='approved' else 'FAIL','- approved mutation')"; else echo 'SKIP - no pending mutation approval'; fi

# 14. merge_request stays blocked
curl -s -X POST http://localhost:8000/execution/github/mutation/ -H 'Content-Type: application/json' -d '{"request_type":"merge_request","title":"t","repo":"t/r","objective":"t"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('execution_mode')=='blocked' else 'FAIL','- merge blocked')"

# 15. Mutation audit events
curl -s http://localhost:8000/audit-logs/ | python3 -c "import sys,json; logs=json.load(sys.stdin); types={l['event_type'] for l in logs}; needed={'github_mutation_requested','github_merge_blocked'}; print('PASS' if not needed-types else 'FAIL','- mutation audit events')"

# 16. Artifact capabilities
curl -s http://localhost:8000/artifacts/capabilities | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if len(d.get('supported_request_types',[]))==4 else 'FAIL','- artifact capabilities')"

# 17. Patch artifact generation
curl -s -X POST http://localhost:8000/artifacts/generate -H 'Content-Type: application/json' -d '{"request_type":"generate_patch_artifact","title":"reg patch","content":"+ test","context":{"filename":"reg.patch"}}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('result',{}).get('status')=='success' and d.get('artifact_id') else 'FAIL','- patch artifact')"

# 18. Diff preview generation
curl -s -X POST http://localhost:8000/artifacts/generate -H 'Content-Type: application/json' -d '{"request_type":"generate_diff_preview","title":"reg diff","content":"diff","context":{"filename":"reg-diff.md"}}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('result',{}).get('status')=='success' and d.get('artifact_id') else 'FAIL','- diff preview')"

# 19. Task artifact listing
TASK_ID=$(curl -s -X POST http://localhost:8000/artifacts/generate -H 'Content-Type: application/json' -d '{"request_type":"generate_patch_artifact","title":"list test","content":"t","context":{"filename":"list.patch"}}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('task_id',''))")
curl -s "http://localhost:8000/artifacts/task/${TASK_ID}" | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if len(d)>=1 else 'FAIL','- task artifact listing')"

# 20. Artifact file retrieval
ART_ID=$(curl -s -X POST http://localhost:8000/artifacts/generate -H 'Content-Type: application/json' -d '{"request_type":"generate_patch_artifact","title":"file test","content":"file-content-check","context":{"filename":"file.patch"}}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('artifact_id',''))")
curl -s "http://localhost:8000/artifacts/file/${ART_ID}" | python3 -c "import sys; c=sys.stdin.read(); print('PASS' if 'file-content-check' in c else 'FAIL','- artifact file retrieval')"

# 21. Artifact audit events
curl -s http://localhost:8000/audit-logs/ | python3 -c "import sys,json; logs=json.load(sys.stdin); types={l['event_type'] for l in logs}; needed={'artifact_requested','artifact_generated'}; print('PASS' if not needed-types else 'FAIL','- artifact audit events')"

# 22. Mutation live-status
curl -s http://localhost:8000/execution/github/mutation/live-status | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'mode' in d else 'FAIL','- mutation live-status')"

# 23. Ops capabilities
curl -s http://localhost:8000/ops/capabilities | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if len(d.get('supported_request_types',[]))==5 else 'FAIL','- ops capabilities')"

# 24. Ops status
curl -s http://localhost:8000/ops/status | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'ops_enabled' in d and 'ops_mode' in d else 'FAIL','- ops status')"

# 25. Maintenance check runs immediately
curl -s -X POST http://localhost:8000/ops/request -H 'Content-Type: application/json' -d '{"request_type":"maintenance_check","title":"t","environment":"dev","context":{}}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('execution_mode')=='ops_stub' and d.get('result',{}).get('status')=='success' else 'FAIL','- maintenance check')"

# 26. Deployment request requires approval
curl -s -X POST http://localhost:8000/ops/request -H 'Content-Type: application/json' -d '{"request_type":"deployment_request","title":"t","environment":"staging","context":{}}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('execution_mode')=='pending_approval' else 'FAIL','- deployment approval')"

# 27. Rollback request requires approval
curl -s -X POST http://localhost:8000/ops/request -H 'Content-Type: application/json' -d '{"request_type":"rollback_request","title":"t","environment":"staging","context":{}}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('execution_mode')=='pending_approval' else 'FAIL','- rollback approval')"

# 28. Approved ops request completes
OPS_APPROVAL=$(curl -s http://localhost:8000/approvals/ | python3 -c "import sys,json; a=[x for x in json.load(sys.stdin) if x['status']=='pending' and x['action_name'].startswith('ops:')]; print(a[-1]['id'] if a else '')")
if [ -n "$OPS_APPROVAL" ]; then curl -s -X POST "http://localhost:8000/approvals/${OPS_APPROVAL}/approve" -H 'Content-Type: application/json' -d '{"decision_notes":"regression"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('status')=='approved' else 'FAIL','- approved ops')"; else echo 'SKIP - no pending ops approval'; fi

# 29. Ops runbooks
curl -s http://localhost:8000/ops/runbooks | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if len(d)>=2 else 'FAIL','- ops runbooks')"

# 30. Ops audit events
curl -s http://localhost:8000/audit-logs/ | python3 -c "import sys,json; logs=json.load(sys.stdin); types={l['event_type'] for l in logs}; needed={'ops_requested','ops_completed'}; print('PASS' if not needed-types else 'FAIL','- ops audit events')"
```
