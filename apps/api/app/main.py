from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import actions, approvals, artifacts, audit_logs, chat, execution, github_execution, github_mutation, mcp, memory, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME} in {settings.APP_ENV}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.9.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])
app.include_router(actions.router, prefix="/actions", tags=["actions"])
app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
app.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit_logs"])
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])
app.include_router(execution.router, prefix="/execution", tags=["execution"])
app.include_router(github_execution.router, prefix="/execution/github", tags=["github_execution"])
app.include_router(github_mutation.router, prefix="/execution/github/mutation", tags=["github_mutation"])
app.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"])


@app.get("/")
def root():
    return {"status": "healthy", "app": settings.APP_NAME, "version": "0.9.0"}
