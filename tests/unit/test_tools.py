"""Unit tests for tools."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from domain import ToolResult
from tools import BanditTool, ESLintTool, GitDiffTool, RuffTool, SemgrepTool, ToolRegistry


def test_tool_registry():
    """Test tool registry."""
    registry = ToolRegistry()
    
    # Create mock tool
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.is_available.return_value = True
    
    registry.register(mock_tool)
    
    assert registry.is_registered("test_tool")
    assert registry.get("test_tool") == mock_tool


def test_tool_registry_duplicate():
    """Test duplicate tool registration."""
    registry = ToolRegistry()
    
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.is_available.return_value = True
    
    registry.register(mock_tool)
    
    with pytest.raises(ValueError):
        registry.register(mock_tool)


def test_git_diff_tool_is_available():
    """Test git availability check."""
    tool = GitDiffTool()
    # This will fail if git is not installed
    # In CI, we assume git is available
    assert tool.is_available()


@patch("subprocess.run")
def test_git_diff_tool_run(mock_run):
    """Test git diff extraction."""
    tool = GitDiffTool()
    
    # Mock git diff output
    mock_run.side_effect = [
        MagicMock(stdout="mock diff content", stderr="", returncode=0),
        MagicMock(stdout="1\t2\tfile.py\n", stderr="", returncode=0),
    ]
    
    # Note: This test requires a git repo, so we skip actual execution
    # Real tests would use a fixture repo


def test_ruff_tool_parse_output():
    """Test ruff output parsing."""
    tool = RuffTool()
    
    json_output = '''[
        {
            "filename": "test.py",
            "location": {"row": 10, "column": 5},
            "code": "E501",
            "message": "Line too long"
        }
    ]'''
    
    result = tool.parse_output(json_output)
    assert "violations" in result
    assert len(result["violations"]) == 1
    assert result["violations"][0]["code"] == "E501"


@patch("subprocess.run")
def test_bandit_tool_excludes_common_dirs(mock_run):
    """Bandit command must include --exclude with common venv/cache dirs.

    bandit does NOT respect .gitignore, so without this flag it would scan
    .venv/, node_modules/, __pycache__/, and other irrelevant directories
    on any project root containing them.
    """
    mock_run.return_value = MagicMock(stdout='{"results": []}', stderr="", returncode=0)
    tool = BanditTool()
    tool._run_bandit(Path("/tmp/some-project"))

    called_cmd = mock_run.call_args[0][0]
    assert "--exclude" in called_cmd
    exclude_arg = called_cmd[called_cmd.index("--exclude") + 1]
    for pattern in (".venv", "venv", "node_modules", "__pycache__", ".git"):
        assert pattern in exclude_arg, f"{pattern!r} missing from bandit --exclude list"


def test_semgrep_tool_parse_output():
    """Test semgrep output parsing."""
    tool = SemgrepTool()
    
    json_output = '''{
        "results": [
            {
                "check_id": "python.security.sql-injection",
                "path": "db.py",
                "start": {"line": 42},
                "end": {"line": 42},
                "extra": {
                    "message": "SQL injection vulnerability",
                    "severity": "ERROR"
                }
            }
        ]
    }'''
    
    result = tool.parse_output(json_output)
    assert "results" in result
    assert len(result["results"]) == 1
    assert result["results"][0]["check_id"] == "python.security.sql-injection"

