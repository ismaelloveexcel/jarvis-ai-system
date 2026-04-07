from app.core.config import settings
from app.mcp.providers.filesystem_provider import MCPFilesystemAdapter
from app.mcp.providers.fetch_provider import MCPFetchAdapter
from app.mcp.providers.github_provider import MCPGitHubReadOnlyAdapter


class MCPRegistry:
    def __init__(self):
        self._tools: dict = {}

        if settings.MCP_FILESYSTEM_ENABLED:
            self._tools["filesystem"] = MCPFilesystemAdapter()

        if settings.MCP_FETCH_ENABLED:
            self._tools["fetch"] = MCPFetchAdapter()

        if settings.MCP_GITHUB_READONLY_ENABLED:
            self._tools["github_readonly"] = MCPGitHubReadOnlyAdapter()

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def get_tool(self, tool_name: str):
        return self._tools.get(tool_name)

    def list_tools(self) -> list[dict]:
        return [
            {"name": name, "enabled": True}
            for name in self._tools.keys()
        ]
