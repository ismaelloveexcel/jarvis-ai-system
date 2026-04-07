from pathlib import Path

from app.core.config import settings
from app.ops.providers.stub_provider import OpsStubProvider
from app.ops.providers.live_safe_provider import OpsLiveSafeProvider


class OpsService:
    def __init__(self):
        if settings.OPS_ENABLED and settings.OPS_MODE == "live_safe":
            self.provider = OpsLiveSafeProvider()
        else:
            self.provider = OpsStubProvider()

    def capabilities(self) -> dict:
        return {
            "enabled": settings.OPS_ENABLED,
            "mode": settings.OPS_MODE,
            "default_environment": settings.OPS_DEFAULT_ENVIRONMENT,
            "supported_request_types": [
                "deployment_request",
                "promote_environment",
                "rollback_request",
                "maintenance_check",
                "runbook_lookup",
            ],
        }

    def status(self) -> dict:
        return {
            "ops_enabled": settings.OPS_ENABLED,
            "ops_mode": settings.OPS_MODE,
            "default_environment": settings.OPS_DEFAULT_ENVIRONMENT,
            "runbooks_available": [p.name for p in Path("docs/runbooks").glob("*.md")],
        }

    def list_runbooks(self) -> list[dict]:
        runbook_dir = Path("docs/runbooks")
        return [
            {"name": p.name, "path": str(p)}
            for p in sorted(runbook_dir.glob("*.md"))
        ]

    def run(self, request_type: str, title: str, environment: str, context: dict) -> dict:
        return self.provider.run(
            request_type=request_type,
            title=title,
            environment=environment,
            context=context,
        )
