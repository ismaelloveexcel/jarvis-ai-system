class MCPExecutionError(Exception):
    pass


class MCPToolAdapter:
    """Base adapter interface for MCP tools.
    Phase 4 providers implement invoke() to either stub or
    call real MCP servers. Phase 5+ can swap in live implementations.
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name

    def invoke(self, payload: dict) -> dict:
        raise NotImplementedError

    def describe(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "parameters": {},
            "description": f"MCP tool: {self.tool_name}",
        }
