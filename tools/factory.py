"""Factory for creating and managing tool instances."""

import subprocess
from app.config import Settings
from app.logging import get_logger
from domain import Language
from tools import BanditTool, CoverageReader, ESLintTool, GitDiffTool, RuffTool, SemgrepTool, ToolRegistry

logger = get_logger(__name__)


def create_tool_registry(settings: Settings, language: Language = Language.PYTHON) -> ToolRegistry:
    """Create and populate tool registry with available tools.

    Args:
        settings: Application settings
        language: Primary programming language
    """
    registry = ToolRegistry()

    # Git diff (required)
    _register_tool(registry, GitDiffTool(), required=True)

    # Language-specific tools
    if language == Language.PYTHON:
        _register_tool(registry, RuffTool(settings.ruff_path))
        _register_tool(registry, BanditTool(settings.bandit_path))
    elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
        _register_tool(registry, ESLintTool(settings.eslint_path))

    # Security tools (language-agnostic)
    _register_tool(registry, SemgrepTool(settings.semgrep_path))

    # Coverage tool (language-agnostic)
    _register_tool(registry, CoverageReader())

    return registry


def _register_tool(registry: ToolRegistry, tool, required: bool = False) -> None:
    """Register a tool, handling errors appropriately."""
    try:
        registry.register(tool)
        logger.info(f"Registered {tool.name} tool")
    except RuntimeError as e:
        if required:
            raise RuntimeError(f"{tool.name} is required but not available")
        # Check why tool is not available
        try:
            subprocess.run(
                [tool.executable_path, "--version"],
                capture_output=True,
                check=True,
                timeout=2
            )
            logger.warning(f"{tool.name} not available: Tool executable found but registration failed")
        except FileNotFoundError:
            logger.warning(f"{tool.name} not available: Executable '{tool.executable_path}' not found in PATH")
        except subprocess.TimeoutExpired:
            logger.warning(f"{tool.name} not available: Executable '{tool.executable_path}' timed out")
        except subprocess.CalledProcessError:
            logger.warning(f"{tool.name} not available: Executable '{tool.executable_path}' returned error")
        except Exception as check_error:
            logger.warning(f"{tool.name} not available: {e} (check error: {check_error})")
