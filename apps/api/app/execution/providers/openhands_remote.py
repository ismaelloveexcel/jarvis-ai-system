import requests
from app.execution.base import ExecutionProvider
from app.core.config import settings


class OpenHandsRemoteProvider(ExecutionProvider):
    def run(self, request_type: str, title: str, objective: str, context: dict) -> dict:
        response = requests.post(
            f"{settings.OPENHANDS_BASE_URL}/execute",
            json={
                "request_type": request_type,
                "title": title,
                "objective": objective,
                "context": context,
            },
            timeout=settings.OPENHANDS_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        data["execution_mode"] = "openhands_remote"
        return data
