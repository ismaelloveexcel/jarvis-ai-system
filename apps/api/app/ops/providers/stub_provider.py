from datetime import datetime

from app.ops.base import OpsProvider, OpsExecutionError


class StubOpsProvider(OpsProvider):
    def run(self, request_type: str, title: str, objective: str, context: dict) -> dict:
        handler = getattr(self, f"_handle_{request_type}", None)
        if not handler:
            raise OpsExecutionError(f"Unknown ops request type: {request_type}")
        return handler(title, objective, context)

    def _handle_maintenance_check(self, title: str, objective: str, context: dict) -> dict:
        environment = context.get("environment", "staging")
        return {
            "status": "ok",
            "mode": "stub",
            "request_type": "maintenance_check",
            "environment": environment,
            "checks": {
                "api_health": "healthy",
                "db_connections": "normal",
                "queue_depth": 0,
                "error_rate": "0.01%",
            },
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Stub maintenance check for {environment}: all systems nominal.",
        }

    def _handle_runbook_lookup(self, title: str, objective: str, context: dict) -> dict:
        runbook_id = context.get("runbook_id", "general-ops")
        return {
            "status": "ok",
            "mode": "stub",
            "request_type": "runbook_lookup",
            "runbook_id": runbook_id,
            "title": f"Runbook: {runbook_id}",
            "steps": [
                "1. Verify environment health",
                "2. Check recent deployments",
                "3. Review error logs",
                "4. Escalate if unresolved",
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Stub runbook lookup for '{runbook_id}'.",
        }

    def _handle_deployment_request(self, title: str, objective: str, context: dict) -> dict:
        environment = context.get("environment", "staging")
        version = context.get("version", "latest")
        artifact_id = context.get("artifact_id")
        return {
            "status": "pending_approval",
            "mode": "stub",
            "request_type": "deployment_request",
            "environment": environment,
            "version": version,
            "artifact_id": artifact_id,
            "deployment_plan": {
                "target": environment,
                "version": version,
                "strategy": "rolling",
                "rollback_available": True,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Stub deployment request for {version} to {environment}. Requires approval.",
        }

    def _handle_promote_environment(self, title: str, objective: str, context: dict) -> dict:
        source = context.get("source_environment", "staging")
        target = context.get("target_environment", "production")
        return {
            "status": "pending_approval",
            "mode": "stub",
            "request_type": "promote_environment",
            "source_environment": source,
            "target_environment": target,
            "promotion_plan": {
                "source": source,
                "target": target,
                "strategy": "blue_green",
                "validation_required": True,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Stub promotion from {source} to {target}. Requires approval.",
        }

    def _handle_rollback_request(self, title: str, objective: str, context: dict) -> dict:
        environment = context.get("environment", "staging")
        rollback_to = context.get("rollback_to_version", "previous")
        return {
            "status": "pending_approval",
            "mode": "stub",
            "request_type": "rollback_request",
            "environment": environment,
            "rollback_to_version": rollback_to,
            "rollback_plan": {
                "target": environment,
                "rollback_to": rollback_to,
                "strategy": "immediate",
                "data_migration_required": False,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Stub rollback to {rollback_to} on {environment}. Requires approval.",
        }
