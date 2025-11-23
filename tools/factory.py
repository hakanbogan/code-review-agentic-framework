"""Factory for creating and managing tool instances."""

from app.config import Settings
from tools import (
    BanditTool,
    CoverageReader,
    ESLintTool,
    GitDiffTool,
    RuffTool,
    SemgrepTool,
    ToolRegistry,
)
from app.logging import get_logger

logger = get_logger(__name__)


def create_tool_registry(settings: Settings) -> ToolRegistry:
    """Create and populate tool registry.

    Args:
        settings: Application settings

    Returns:
        Configured ToolRegistry with available tools
    """
    registry = ToolRegistry()

    # Git diff (required)
    git_tool = GitDiffTool()
    try:
        registry.register(git_tool)
        logger.info("Registered git_diff tool")
    except RuntimeError as e:
        logger.error(f"Failed to register git_diff: {e}")
        raise RuntimeError("Git is required but not available")

    # Python tools
    try:
        ruff_tool = RuffTool(settings.ruff_path)
        registry.register(ruff_tool)
        logger.info("Registered ruff tool")
    except RuntimeError as e:
        logger.warning(f"Ruff not available: {e}")

    try:
        bandit_tool = BanditTool(settings.bandit_path)
        registry.register(bandit_tool)
        logger.info("Registered bandit tool")
    except RuntimeError as e:
        logger.warning(f"Bandit not available: {e}")

    # JavaScript/TypeScript tools
    try:
        eslint_tool = ESLintTool(settings.eslint_path)
        registry.register(eslint_tool)
        logger.info("Registered eslint tool")
    except RuntimeError as e:
        logger.warning(f"ESLint not available: {e}")

    # Security tools
    try:
        semgrep_tool = SemgrepTool(settings.semgrep_path)
        registry.register(semgrep_tool)
        logger.info("Registered semgrep tool")
    except RuntimeError as e:
        logger.warning(f"Semgrep not available: {e}")

    # Coverage reader (always available)
    coverage_tool = CoverageReader()
    registry.register(coverage_tool)
    logger.info("Registered coverage_reader tool")

    return registry
