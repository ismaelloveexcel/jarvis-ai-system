from app.mcp.base import MCPToolAdapter


class MCPFetchAdapter(MCPToolAdapter):
    def __init__(self):
        super().__init__("fetch")

    def invoke(self, payload: dict) -> dict:
        return {
            "status": "success",
            "execution_mode": "mcp",
            "tool_name": self.tool_name,
            "note": "Fetch MCP adapter invoked. Real MCP server integration available in Phase 5+.",
            "payload_received": payload,
        }
