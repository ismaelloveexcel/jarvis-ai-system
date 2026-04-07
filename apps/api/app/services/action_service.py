from app.core.config import settings
from app.actions.action_registry import ActionRegistry
from app.services.mcp_service import MCPService

ACTION_TO_MCP_TOOL = {
    "create_file": "filesystem",
    "read_file": "filesystem",
    "http_request": "fetch",
    "github_repo_info_stub": "github_readonly",
}


class ActionService:
    def __init__(self):
        self.local_registry = ActionRegistry()
        self.mcp_service = MCPService()

    def resolve_execution_mode(self, action_name: str) -> str:
        if not settings.MCP_ENABLED:
            return "local"
        if settings.MCP_DEFAULT_MODE != "mcp":
            return "local"

        tool_name = ACTION_TO_MCP_TOOL.get(action_name)
        if not tool_name:
            return "local"

        if self.mcp_service.registry.has_tool(tool_name):
            return "mcp"

        return "local"

    def run_action(self, action_name: str, payload: dict) -> dict:
        mode = self.resolve_execution_mode(action_name)

        if mode == "mcp":
            tool_name = ACTION_TO_MCP_TOOL[action_name]
            result = self.mcp_service.execute(tool_name=tool_name, payload=payload)
            result["execution_mode"] = "mcp"
            result["action_name"] = action_name
            return result

        result = self.local_registry.execute(action_name=action_name, payload=payload)
        result["execution_mode"] = "local"
        return result

    def list_actions(self) -> list[dict]:
        return self.local_registry.list_actions()
