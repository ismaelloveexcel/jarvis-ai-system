from pydantic import BaseModel


class MCPStatusResponse(BaseModel):
    enabled: bool
    default_mode: str
    filesystem_enabled: bool
    fetch_enabled: bool
    github_readonly_enabled: bool


class MCPToolInfo(BaseModel):
    name: str
    enabled: bool
    mode: str
    description: str
