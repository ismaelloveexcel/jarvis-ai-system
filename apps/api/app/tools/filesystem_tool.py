import os
from pathlib import Path

# Inside Docker: /app/workspace (mounted volume)
# Local dev: repo_root/workspace/generated
_env_base = os.environ.get("JARVIS_WORKSPACE_DIR", "")
if _env_base:
    SAFE_BASE_DIR = Path(_env_base)
else:
    SAFE_BASE_DIR = Path(__file__).resolve().parents[3] / "workspace" / "generated"

SAFE_BASE_DIR.mkdir(parents=True, exist_ok=True)


def safe_write_file(relative_path: str, content: str) -> dict:
    target = (SAFE_BASE_DIR / relative_path).resolve()

    if not str(target).startswith(str(SAFE_BASE_DIR.resolve())):
        raise ValueError("Unsafe path detected")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return {
        "status": "success",
        "action": "create_file",
        "path": str(target),
        "bytes_written": len(content.encode("utf-8")),
    }


def safe_read_file(relative_path: str) -> dict:
    target = (SAFE_BASE_DIR / relative_path).resolve()

    if not str(target).startswith(str(SAFE_BASE_DIR.resolve())):
        raise ValueError("Unsafe path detected")

    if not target.exists():
        raise FileNotFoundError(f"File not found: {relative_path}")

    content = target.read_text(encoding="utf-8")
    return {
        "status": "success",
        "action": "read_file",
        "path": str(target),
        "content": content,
    }
