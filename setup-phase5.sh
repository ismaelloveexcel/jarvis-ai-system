#!/bin/bash
# =============================================================================
# Jarvis Assistant – Phase 5 Bootstrap Script
# Adds:
# - OpenHands config layer
# - OpenHands client/service abstraction
# - execution request routing
# - execution endpoints
# - OpenHands audit logging
# - minimal frontend execution UI
#
# Assumes Phase 4 already exists in current repo root.
# Run once:
#   bash setup-phase5.sh
# =============================================================================

set -euo pipefail

PROJECT_ROOT="."
cd "${PROJECT_ROOT}"

echo "🚀 Starting Jarvis Phase 5 bootstrap..."

mkdir -p apps/api/app/execution
mkdir -p apps/api/app/execution/providers
mkdir -p apps/api/app/services
mkdir -p apps/api/app/routers
mkdir -p apps/api/app/schemas

# -----------------------------------------------------------------------------
# .env.example extension
# -----------------------------------------------------------------------------

if ! grep -q "^OPENHANDS_ENABLED=" .env.example; then
  cat >> .env.example << 'EOF'

# -----------------------------------------------------------------------------
# OpenHands
# -----------------------------------------------------------------------------
OPENHANDS_ENABLED=false
OPENHANDS_MODE=stub
OPENHANDS_BASE_URL=http://localhost:3001
OPENHANDS_TIMEOUT_SECONDS=60
EOF
fi

echo "✅ Phase 5 directories and .env.example updated."
