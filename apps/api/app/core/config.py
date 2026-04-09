from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "Jarvis Assistant"
    SECRET_KEY: str = "change-me"

    API_KEY: str = ""
    RATE_LIMIT: str = "60/minute"

    DATABASE_URL: str = "postgresql://jarvis:changeme123@postgres:5432/jarvis_db"

    LLM_PROVIDER: Literal["openai", "anthropic", "xai"] = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: str = ""

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    XAI_API_KEY: str = ""

    MCP_ENABLED: bool = False
    MCP_DEFAULT_MODE: Literal["local", "mcp"] = "local"
    MCP_FILESYSTEM_ENABLED: bool = False
    MCP_FETCH_ENABLED: bool = False
    MCP_GITHUB_READONLY_ENABLED: bool = False

    OPENHANDS_ENABLED: bool = False
    OPENHANDS_MODE: Literal["stub", "remote"] = "stub"
    OPENHANDS_BASE_URL: str = "http://localhost:3001"
    OPENHANDS_TIMEOUT_SECONDS: int = 60

    GITHUB_EXECUTION_ENABLED: bool = True
    GITHUB_EXECUTION_MODE: Literal["readonly", "proposal", "approval_required_write"] = "readonly"
    GITHUB_DEFAULT_REPO: str = ""
    GITHUB_TOKEN: str = ""

    GITHUB_MUTATION_ENABLED: bool = False
    GITHUB_MUTATION_MODE: Literal["stub", "live"] = "stub"
    GITHUB_DEFAULT_BASE_BRANCH: str = "main"
    GITHUB_DEFAULT_DRAFT_PR: bool = True
    GITHUB_MUTATION_LIVE_ENABLED: bool = False
    GITHUB_ALLOWED_WRITE_REPOS: str = ""

    OPS_ENABLED: bool = True
    OPS_MODE: Literal["stub", "live_safe"] = "stub"
    OPS_DEFAULT_ENVIRONMENT: Literal["dev", "staging", "production"] = "dev"
    OPS_ALLOW_LIVE_MAINTENANCE: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
