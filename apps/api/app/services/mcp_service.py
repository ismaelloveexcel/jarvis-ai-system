from app.core.config import settings
from app.mcp.registry import MCPRegistry


class MCPService:
    def __init__(self):
        self.registry = MCPRegistry()

    def get_status(self) -> dict:
        return {
            "enabled": settings.MCP_ENABLED,
            "default_mode": settings.MCP_DEFAULT_MODE,
            "filesystem_enabled": settings.MCP_FILESYSTEM_ENABLED,
            "fetch_enabled": settings.MCP_FETCH_ENABLED,
            "github_readonly_enabled": settings.MCP_GITHUB_READONLY_ENABLED,
        }

    def list_tools(self) -> list[dict]:
        tools = self.registry.list_tools()
        descriptions = {
            "filesystem": "MCP-backed filesystem capability",
            "fetch": "MCP-backed fetch/web retrieval capability",
            "github_readonly": "MCP-backed GitHub read-only capability",
        }
        return [
            {
                "name": tool["name"],
                "enabled": tool["enabled"],
                "mode": "mcp",
                "description": descriptions.get(tool["name"], "MCP tool"),
            }
            for tool in tools
        ]

    def execute(self, tool_name: str, payload: dict) -> dict:
        adapter = self.registry.get_tool(tool_name)
        if not adapter:
            raise ValueError(f"MCP tool '{tool_name}' is not enabled")
        return adapter.invoke(payload)
