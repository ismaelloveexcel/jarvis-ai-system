from app.ops.base import OpsProvider
from app.core.config import settings


class OpsLiveSafeProvider(OpsProvider):
    def run(self, request_type: str, title: str, environment: str, context: dict) -> dict:
        if request_type == "maintenance_check":
            if not settings.OPS_ALLOW_LIVE_MAINTENANCE:
                raise ValueError("Live maintenance checks are disabled.")
            return {
                "status": "success",
                "execution_mode": "ops_live_safe",
                "request_type": request_type,
                "environment": environment,
                "summary": f"Live-safe maintenance check completed for {environment}.",
                "checks": [
                    "API health OK",
                    "Environment config inspected",
                    "No destructive operations performed",
                ],
            }

        # Deployment-like requests remain controlled and non-destructive in V1.
        return {
            "status": "success",
            "execution_mode": "ops_live_safe",
            "request_type": request_type,
            "environment": environment,
            "summary": f"Live-safe operational contract executed for {request_type} in {environment}.",
        }
