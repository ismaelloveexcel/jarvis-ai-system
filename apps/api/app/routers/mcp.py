import logging

from fastapi import APIRouter, HTTPException
from app.schemas.mcp import MCPStatusResponse, MCPToolInfo
from app.services.mcp_service import MCPService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/status", response_model=MCPStatusResponse)
def get_mcp_status():
    try:
        status = MCPService().get_status()
        return MCPStatusResponse(**status)
    except Exception as exc:
        logger.exception("get_mcp_status failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/tools", response_model=list[MCPToolInfo])
def list_mcp_tools():
    try:
        tools = MCPService().list_tools()
        return [MCPToolInfo(**tool) for tool in tools]
    except Exception as exc:
        logger.exception("list_mcp_tools failed")
        raise HTTPException(status_code=500, detail=str(exc))
