from app.execution.base import ExecutionProvider


class OpenHandsStubProvider(ExecutionProvider):
    def run(self, request_type: str, title: str, objective: str, context: dict) -> dict:
        return {
            "status": "success",
            "execution_mode": "openhands_stub",
            "request_type": request_type,
            "title": title,
            "objective": objective,
            "summary": f"Stubbed OpenHands run completed for '{title}'.",
            "generated_plan": [
                "Analyze request",
                "Plan repo/file changes",
                "Prepare implementation output",
                "Return structured result"
            ],
            "context": context,
        }
