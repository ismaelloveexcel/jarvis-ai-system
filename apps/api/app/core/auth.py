from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Depends(_api_key_header)):
    if not settings.API_KEY:
        return
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
