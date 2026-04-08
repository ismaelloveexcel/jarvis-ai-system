from app.mcp.base import MCPToolAdapter, MCPExecutionError
from app.tools.filesystem_tool import safe_read_file, safe_write_file, SAFE_BASE_DIR


class MCPFilesystemAdapter(MCPToolAdapter):
    def __init__(self):
        super().__init__("filesystem")

    def invoke(self, payload: dict) -> dict:
        operation = payload.get("operation")

        if operation == "read":
            path = payload.get("path")
            if not path:
                raise MCPExecutionError("Missing 'path' for read operation")
            return safe_read_file(path)

        if operation == "write":
            path = payload.get("path")
            content = payload.get("content", "")
            if not path:
                raise MCPExecutionError("Missing 'path' for write operation")
            return safe_write_file(path, content)

        if operation == "list":
            subdir = payload.get("path", "")
            safe_base = SAFE_BASE_DIR.resolve()
            target = (safe_base / subdir).resolve()
            if not target.is_relative_to(safe_base):
                raise MCPExecutionError("Unsafe path detected")
            if not target.exists():
                return {"status": "success", "action": "list", "path": str(target), "entries": []}
            if not target.is_dir():
                raise MCPExecutionError(f"Path is not a directory: {target}")
            entries = []
            for item in sorted(target.iterdir()):
                entries.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                })
            return {"status": "success", "action": "list", "path": str(target), "entries": entries}

        raise MCPExecutionError(f"Unknown filesystem operation: {operation}. Supported: read, write, list")

    def describe(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "parameters": {
                "operation": "read | write | list",
                "path": "Relative path within workspace",
                "content": "(write only) File content to write",
            },
            "description": "MCP filesystem tool: read, write, and list files within the safe workspace directory",
        }
