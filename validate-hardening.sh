#!/bin/bash
set -e

echo "=== Jarvis V1 Hardening Validation Script ==="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_count=0
pass_count=0

check() {
  check_count=$((check_count + 1))
  echo -n "[Check $check_count] $1 ... "
}

pass() {
  pass_count=$((pass_count + 1))
  echo -e "${GREEN}PASS${NC}"
}

fail() {
  echo -e "${RED}FAIL${NC}: $1"
}

warn() {
  echo -e "${YELLOW}WARN${NC}: $1"
}

echo "### Stage 1: Secrets Hardening ###"
echo ""

# 1. Check SECRET_KEY is empty in config
check "config.py SECRET_KEY default is empty"
if grep -q 'SECRET_KEY: str = ""' apps/api/app/core/config.py; then
  pass
else
  fail "SECRET_KEY still has default value"
  exit 1
fi

# 2. Check docker-compose uses env var for password
check "docker-compose POSTGRES_PASSWORD uses env var"
if grep -q 'POSTGRES_PASSWORD: \${POSTGRES_PASSWORD' docker-compose.yml; then
  pass
else
  fail "POSTGRES_PASSWORD not using env var"
  exit 1
fi

# 3. Check redis added to docker-compose
check "redis service in docker-compose"
if grep -q 'image: redis:7-alpine' docker-compose.yml; then
  pass
else
  fail "Redis service missing"
  exit 1
fi

# 4. Check Celery broker URL in config
check "Celery broker/backend URL in config"
if grep -q 'CELERY_BROKER_URL' apps/api/app/core/config.py; then
  pass
else
  fail "Celery config missing"
  exit 1
fi

# 5. Check requirements has Celery and Redis
check "requirements.txt includes celery and redis"
if grep -q 'celery\[redis\]' apps/api/requirements.txt && grep -q 'redis==' apps/api/requirements.txt; then
  pass
else
  fail "Celery/Redis not in requirements"
  exit 1
fi

# 6. Check .env.example is updated
check ".env.example has no hardcoded credentials"
if ! grep -q 'changeme123' .env.example; then
  pass
else
  warn ".env.example still has old password (check .env.local)"
fi

echo ""
echo "### Stage 2: Background Task Durability ###"
echo ""

# 7. Check Celery app exists
check "Celery app module exists"
if [ -f "apps/api/app/tasks/celery_app.py" ]; then
  pass
else
  fail "Celery app not found"
  exit 1
fi

# 8. Check Celery tasks exist
check "Celery task modules created"
if [ -f "apps/api/app/tasks/execution.py" ] && [ -f "apps/api/app/tasks/github_mutation.py" ] && [ -f "apps/api/app/tasks/ops.py" ]; then
  pass
else
  fail "One or more task modules missing"
  exit 1
fi

# 9. Check tasks have retry logic
check "Celery tasks include retry logic"
if grep -q 'max_retries' apps/api/app/tasks/github_mutation.py; then
  pass
else
  fail "Retry logic not found in tasks"
fi

echo ""
echo "### Stage 3: Database Migrations ###"
echo ""

# 10. Check main.py runs migrations on startup
check "main.py auto-runs migrations"
if grep -q '"alembic", "upgrade", "head"' apps/api/app/main.py; then
  pass
else
  fail "Migration auto-run not in main.py"
fi

# 11. Check migration files exist
check "New migration files created"
if ls apps/api/alembic/versions/b1c2d3e4f5g6_*.py 2>/dev/null && ls apps/api/alembic/versions/c1d2e3f4g5h6_*.py 2>/dev/null; then
  pass
else
  warn "Expected migration files not found with exact names (may have different timestamps)"
fi

echo ""
echo "### Stage 4: Approval Model & Schema ###"
echo ""

# 12. Check Approval model has new fields
check "Approval model has approved_by field"
if grep -q 'approved_by.*Mapped' apps/api/app/models/approval.py; then
  pass
else
  fail "Approval model missing approved_by"
  exit 1
fi

check "Approval model has approved_at field"
if grep -q 'approved_at.*Mapped' apps/api/app/models/approval.py; then
  pass
else
  fail "Approval model missing approved_at"
  exit 1
fi

# 13. Check ApprovalResponse schema updated
check "ApprovalResponse has approved_by field"
if grep -q 'approved_by:.*None' apps/api/app/schemas/approval.py; then
  pass
else
  fail "ApprovalResponse missing approved_by"
fi

# 14. Check ApprovalService.approve() updated
check "ApprovalService.approve() accepts approved_by_user_id"
if grep -q 'approved_by_user_id' apps/api/app/services/approval_service.py; then
  pass
else
  fail "ApprovalService not updated"
fi

echo ""
echo "### Stage 5: Input Validation ###"
echo ""

# 15. Check guardrails has size validation
check "Guardrails service has _check_payload_size()"
if grep -q '_check_payload_size' apps/api/app/guardrails/service.py; then
  pass
else
  fail "Payload size check missing from guardrails"
fi

# 16. Check schema validation on request payloads
check "Schemas have max_length and size validation"
if grep -q 'max_length\|65536' apps/api/app/schemas/*.py 2>/dev/null; then
  pass
else
  warn "Schema validation not clearly visible (may be in validators)"
fi

echo ""
echo "### Stage 6: Frontend Updates ###"
echo ""

# 17. Check ApprovalDetail component exists
check "ApprovalDetail component created"
if [ -f "apps/web/components/ApprovalDetail.tsx" ]; then
  pass
else
  fail "ApprovalDetail.tsx not found"
fi

# 18. Check page.tsx imports ApprovalDetail
check "page.tsx imports ApprovalDetail"
if grep -q 'import.*ApprovalDetail' apps/web/app/page.tsx; then
  pass
else
  warn "ApprovalDetail not imported in page.tsx (may need manual integration)"
fi

echo ""
echo "=== Final Results ==="
echo "Passed: $pass_count / $check_count checks"
echo ""

if [ $pass_count -ge $((check_count - 2)) ]; then
  echo -e "${GREEN}✓ Hardening validation largely complete${NC}"
  echo ""
  echo "Next steps:"
  echo "  1. Create .env file from .env.example with your API keys"
  echo "  2. Set POSTGRES_PASSWORD in .env if custom password is desired"
  echo "  3. Run migrations: docker compose exec -it api alembic upgrade head"
  echo "  4. Start Celery worker: celery -A app.tasks.celery_app worker -l info"
  echo "  5. Run tests: docker compose exec -it api pytest tests/ -v"
  echo "  6. Verify ApprovalDetail UI integration manually"
  echo ""
  exit 0
else
  echo -e "${RED}✗ Some critical checks failed${NC}"
  exit 1
fi
