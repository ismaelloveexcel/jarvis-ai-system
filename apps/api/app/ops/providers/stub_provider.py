from app.ops.base import OpsProvider


class OpsStubProvider(OpsProvider):
    def run(self, request_type: str, title: str, environment: str, context: dict) -> dict:
        if request_type == "maintenance_check":
            return {
                "status": "success",
                "execution_mode": "ops_stub",
                "request_type": request_type,
                "environment": environment,
                "summary": f"Stub maintenance check completed for {environment}.",
                "checks": [
                    "API health OK",
                    "Frontend reachable",
                    "Database reachable",
                ],
            }

        if request_type == "runbook_lookup":
            return {
                "status": "success",
                "execution_mode": "ops_stub",
                "request_type": request_type,
                "environment": environment,
                "summary": f"Runbook lookup completed for {environment}.",
                "runbook": context.get("runbook", "general-ops.md"),
            }

        if request_type == "deployment_request":
            return {
                "status": "success",
                "execution_mode": "ops_stub",
                "request_type": request_type,
                "environment": environment,
                "summary": f"Stub deployment request executed for {environment}.",
            }

        if request_type == "promote_environment":
            return {
                "status": "success",
                "execution_mode": "ops_stub",
                "request_type": request_type,
                "environment": environment,
                "summary": f"Stub environment promotion executed toward {environment}.",
            }

        if request_type == "rollback_request":
            return {
                "status": "success",
                "execution_mode": "ops_stub",
                "request_type": request_type,
                "environment": environment,
                "summary": f"Stub rollback request executed for {environment}.",
            }

        raise ValueError(f"Unsupported ops request type: {request_type}")
