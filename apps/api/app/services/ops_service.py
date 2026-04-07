import os
import glob

from app.core.config import settings
from app.ops.providers.stub_provider import StubOpsProvider
from app.ops.providers.live_safe_provider import LiveSafeOpsProvider


SUPPORTED_OPS_TYPES = [
    "deployment_request",
    "promote_environment",
    "rollback_request",
    "maintenance_check",
    "runbook_lookup",
]


class OpsService:
    def __init__(self):
        if settings.OPS_MODE == "live_safe":
            self._provider = LiveSafeOpsProvider()
        else:
            self._provider = StubOpsProvider()

    def capabilities(self) -> dict:
        return {
            "enabled": settings.OPS_ENABLED,
            "mode": settings.OPS_MODE,
            "default_environment": settings.OPS_DEFAULT_ENVIRONMENT,
            "allow_live_maintenance": settings.OPS_ALLOW_LIVE_MAINTENANCE,
            "supported_types": SUPPORTED_OPS_TYPES,
        }

    def status(self) -> dict:
        return {
            "enabled": settings.OPS_ENABLED,
            "mode": settings.OPS_MODE,
            "default_environment": settings.OPS_DEFAULT_ENVIRONMENT,
            "allow_live_maintenance": settings.OPS_ALLOW_LIVE_MAINTENANCE,
        }

    def list_runbooks(self) -> list[dict]:
        runbooks_dir = os.environ.get("RUNBOOKS_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "runbooks"))
        runbooks_dir = os.path.normpath(runbooks_dir)
        results = []

        if not os.path.isdir(runbooks_dir):
            return results

        for filepath in sorted(glob.glob(os.path.join(runbooks_dir, "*.md"))):
            filename = os.path.basename(filepath)
            runbook_id = filename.replace(".md", "")
            title = runbook_id.replace("-", " ").title()
            description = ""

            try:
                with open(filepath, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        stripped = line.strip()
                        if stripped.startswith("# "):
                            title = stripped[2:]
                        elif stripped and not stripped.startswith("#") and not description:
                            description = stripped
            except OSError:
                pass

            results.append({
                "runbook_id": runbook_id,
                "title": title,
                "description": description,
                "steps": [],
            })

        return results

    def run(self, request_type: str, title: str, objective: str, context: dict) -> dict:
        return self._provider.run(
            request_type=request_type,
            title=title,
            objective=objective,
            context=context,
        )
