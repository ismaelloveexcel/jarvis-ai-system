from app.core.config import settings
from app.execution.providers.openhands_stub import OpenHandsStubProvider
from app.execution.providers.openhands_remote import OpenHandsRemoteProvider


class OpenHandsService:
    def __init__(self):
        if settings.OPENHANDS_MODE == "remote" and settings.OPENHANDS_ENABLED:
            self.provider = OpenHandsRemoteProvider()
        else:
            self.provider = OpenHandsStubProvider()

    def run(self, request_type: str, title: str, objective: str, context: dict) -> dict:
        return self.provider.run(
            request_type=request_type,
            title=title,
            objective=objective,
            context=context,
        )

    def capabilities(self) -> dict:
        return {
            "enabled": settings.OPENHANDS_ENABLED,
            "mode": settings.OPENHANDS_MODE,
            "base_url": settings.OPENHANDS_BASE_URL,
            "supported_request_types": [
                "code_generation",
                "repo_scaffold",
                "file_refactor",
                "bug_fix_plan",
            ],
        }
