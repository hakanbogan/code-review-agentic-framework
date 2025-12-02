"""Factory for creating and managing tool instances."""

from app.config import Settings
from app.logging import get_logger
from tools import BanditTool, CoverageReader, ESLintTool, GitDiffTool, RuffTool, SemgrepTool, ToolRegistry

logger = get_logger(__name__)


def create_tool_registry(settings: Settings) -> ToolRegistry:
    """Create and populate tool registry with available tools."""
    registry = ToolRegistry()

    # Git diff (required)
    _register_tool(registry, GitDiffTool(), required=True)

    # Optional tools
    _register_tool(registry, RuffTool(settings.ruff_path))
    _register_tool(registry, BanditTool(settings.bandit_path))
    _register_tool(registry, ESLintTool(settings.eslint_path))
    _register_tool(registry, SemgrepTool(settings.semgrep_path))
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
        logger.warning(f"{tool.name} not available: {e}")
