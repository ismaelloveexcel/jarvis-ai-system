from app.tools.filesystem_tool import safe_write_file, safe_read_file
from app.tools.http_tool import safe_http_get
from app.tools.github_tool import github_repo_info_stub

AVAILABLE_ACTIONS = [
    {
        "name": "create_file",
        "description": "Create or overwrite a file under the controlled workspace directory",
        "required_params": ["relative_path", "content"],
    },
    {
        "name": "read_file",
        "description": "Read a file from the controlled workspace directory",
        "required_params": ["relative_path"],
    },
    {
        "name": "http_request",
        "description": "Perform a safe outbound HTTP GET request",
        "required_params": ["url"],
    },
    {
        "name": "github_repo_info_stub",
        "description": "Return structured stub info for a GitHub repo (no real API call)",
        "required_params": ["repo"],
    },
]


class ActionRegistry:
    def list_actions(self) -> list[dict]:
        return AVAILABLE_ACTIONS

    def execute(self, action_name: str, payload: dict) -> dict:
        if action_name == "create_file":
            return safe_write_file(
                relative_path=payload["relative_path"],
                content=payload["content"],
            )

        if action_name == "read_file":
            return safe_read_file(
                relative_path=payload["relative_path"],
            )

        if action_name == "http_request":
            return safe_http_get(
                url=payload["url"],
                timeout=payload.get("timeout", 15),
            )

        if action_name == "github_repo_info_stub":
            return github_repo_info_stub(
                repo=payload["repo"],
            )

        raise ValueError(f"Unknown action: {action_name}")
