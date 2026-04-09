import logging
import subprocess
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import text

from app.core.auth import require_api_key
from app.core.config import settings
from app.core.logging import RequestIdMiddleware, setup_logging
from app.db.session import SessionLocal
from app.routers import (
    actions, approvals, artifacts, audit_logs, chat,
    execution, github_execution, github_mutation, mcp, memory, ops, tasks,
)

logger = logging.getLogger("jarvis")

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("starting", extra={"app": settings.APP_NAME, "env": settings.APP_ENV})
    
    # Run Alembic migrations on startup
    try:
        logger.info("Running database migrations...")
        default_cwd = Path("/app")
        local_cwd = Path(__file__).resolve().parents[2]
        alembic_cwd = default_cwd if default_cwd.exists() else local_cwd
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(alembic_cwd),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            logger.warning(
                "Alembic migration completed with warnings: %s", result.stderr
            )
        else:
            logger.info("Database migrations completed successfully")
    except subprocess.TimeoutExpired:
        logger.warning("Database migration timeout (60s); continuing startup")
    except Exception as exc:
        logger.error("Failed to run migrations: %s", exc)
    
    yield


_auth = [Depends(require_api_key)]

# When an API key is required, disable interactive docs to prevent unauthenticated access
_protected = bool(settings.API_KEY)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.10.0",
    lifespan=lifespan,
    docs_url=None if _protected else "/docs",
    redoc_url=None if _protected else "/redoc",
    openapi_url=None if _protected else "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["chat"], dependencies=_auth)
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"], dependencies=_auth)
app.include_router(memory.router, prefix="/memory", tags=["memory"], dependencies=_auth)
app.include_router(actions.router, prefix="/actions", tags=["actions"], dependencies=_auth)
app.include_router(approvals.router, prefix="/approvals", tags=["approvals"], dependencies=_auth)
app.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit_logs"], dependencies=_auth)
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"], dependencies=_auth)
app.include_router(execution.router, prefix="/execution", tags=["execution"], dependencies=_auth)
app.include_router(github_execution.router, prefix="/execution/github", tags=["github_execution"], dependencies=_auth)
app.include_router(github_mutation.router, prefix="/execution/github/mutation", tags=["github_mutation"], dependencies=_auth)
app.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"], dependencies=_auth)
app.include_router(ops.router, prefix="/ops", tags=["ops"], dependencies=_auth)


def _check_db() -> bool:
    db = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        if db is not None:
            db.close()


@app.get("/")
@limiter.exempt
def root():
    db_ok = _check_db()
    status = "healthy" if db_ok else "degraded"
    code = 200 if db_ok else 503
    return JSONResponse(
        status_code=code,
        content={
            "status": status,
            "app": settings.APP_NAME,
            "version": "0.10.0",
            "database": "connected" if db_ok else "unavailable",
        },
    )


@app.get("/health")
@limiter.exempt
def health():
    db_ok = _check_db()
    status = "healthy" if db_ok else "unhealthy"
    code = 200 if db_ok else 503
    return JSONResponse(
        status_code=code,
        content={"status": status, "database": "connected" if db_ok else "unavailable"},
    )
