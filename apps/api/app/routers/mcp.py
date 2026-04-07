from fastapi import APIRouter
from app.schemas.mcp import MCPStatusResponse, MCPToolInfo
from app.services.mcp_service import MCPService

router = APIRouter()


@router.get("/status", response_model=MCPStatusResponse)
def get_mcp_status():
    status = MCPService().get_status()
    return MCPStatusResponse(**status)


@router.get("/tools", response_model=list[MCPToolInfo])
def list_mcp_tools():
    tools = MCPService().list_tools()
    return [MCPToolInfo(**tool) for tool in tools]
