"""Tests for MCP filesystem provider."""
import os
from app.mcp.providers.filesystem_provider import MCPFilesystemAdapter
from app.mcp.base import MCPExecutionError
from app.tools.filesystem_tool import SAFE_BASE_DIR
import pytest


@pytest.fixture(autouse=True)
def cleanup_test_files():
    yield
    test_file = SAFE_BASE_DIR / "mcp_test_file.txt"
    if test_file.exists():
        test_file.unlink()


def test_filesystem_write():
    adapter = MCPFilesystemAdapter()
    result = adapter.invoke({"operation": "write", "path": "mcp_test_file.txt", "content": "hello"})
    assert result["status"] == "success"
    assert result["bytes_written"] == 5


def test_filesystem_read():
    adapter = MCPFilesystemAdapter()
    adapter.invoke({"operation": "write", "path": "mcp_test_file.txt", "content": "read me"})
    result = adapter.invoke({"operation": "read", "path": "mcp_test_file.txt"})
    assert result["status"] == "success"
    assert result["content"] == "read me"


def test_filesystem_list():
    adapter = MCPFilesystemAdapter()
    adapter.invoke({"operation": "write", "path": "mcp_test_file.txt", "content": "listed"})
    result = adapter.invoke({"operation": "list", "path": ""})
    assert result["status"] == "success"
    names = [e["name"] for e in result["entries"]]
    assert "mcp_test_file.txt" in names


def test_filesystem_read_missing():
    adapter = MCPFilesystemAdapter()
    with pytest.raises(FileNotFoundError):
        adapter.invoke({"operation": "read", "path": "nonexistent_file_xyz.txt"})


def test_filesystem_unknown_operation():
    adapter = MCPFilesystemAdapter()
    with pytest.raises(MCPExecutionError, match="Unknown filesystem operation"):
        adapter.invoke({"operation": "delete", "path": "file.txt"})


def test_filesystem_missing_path_on_write():
    adapter = MCPFilesystemAdapter()
    with pytest.raises(MCPExecutionError, match="Missing 'path'"):
        adapter.invoke({"operation": "write", "content": "no path"})


def test_filesystem_describe():
    adapter = MCPFilesystemAdapter()
    desc = adapter.describe()
    assert desc["tool_name"] == "filesystem"
    assert "read" in desc["parameters"]["operation"]
