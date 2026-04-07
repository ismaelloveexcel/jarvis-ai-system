# Deployment Runbook

Procedures for deploying new versions of the Jarvis AI system.

## Pre-Deployment

1. Ensure all regression checks pass (see `docs/regression-checklist.md`)
2. Tag the current stable state: `git tag phaseN-stable`
3. Verify no pending approvals in the system
4. Confirm target environment is healthy via maintenance check

## Deployment Steps

1. Submit deployment request via `/ops/request` with type `deployment_request`
2. Specify target environment and version in context
3. Await approval from operations lead
4. Monitor deployment progress via task status
5. Run smoke tests against deployed environment

## Post-Deployment

1. Verify all endpoints respond correctly
2. Check audit logs for any errors
3. Monitor error rates for 15 minutes
4. If issues detected, initiate rollback procedure

## Environment Promotion

1. Validate staging environment is stable
2. Submit promote request via `/ops/request` with type `promote_environment`
3. Specify source and target environments
4. Await approval
5. Verify production health after promotion
