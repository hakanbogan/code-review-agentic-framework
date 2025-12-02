"""Context builder for PR reviews."""

from pathlib import Path
from typing import Dict
from uuid import uuid4

from app.logging import get_logger
from domain import PRContext, PRMetadata, ToolResult
from tools import ToolRegistry

logger = get_logger(__name__)


class ContextBuilder:
    """Builds complete context for PR review."""

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry

    def build_context(
        self,
        pr_metadata: PRMetadata,
        repo_path: Path,
        base_ref: str = "HEAD",
        compare_ref: str | None = None,
    ) -> PRContext:
        """Build complete PR context with tool results."""
        correlation_id = uuid4()
        logger.info(f"Building context for PR {pr_metadata.pr_id}", extra={"correlation_id": str(correlation_id)})

        # Extract git diff
        diff_result = self._run_tool("git_diff", repo_path, base_ref=base_ref, compare_ref=compare_ref)
        if not diff_result.success:
            raise RuntimeError(f"Failed to extract git diff: {diff_result.errors}")

        # Build tool results
        tool_results = {"git_diff": diff_result}
        tool_results.update(self._run_language_tools(pr_metadata.language, repo_path))

        logger.info(f"Context built with {len(tool_results)} tool results")

        return PRContext(
            correlation_id=correlation_id,
            pr_metadata=pr_metadata,
            diff_content=diff_result.output or "",
            tool_results=tool_results,
        )

    def _run_language_tools(self, language: str, repo_path: Path) -> Dict[str, ToolResult]:
        """Run language-specific and security tools."""
        results = {}

        # Language-specific tools
        language_tools = {
            "python": ["ruff", "bandit"],
            "javascript": ["eslint"],
            "typescript": ["eslint"],
        }

        for tool_name in language_tools.get(language, []):
            result = self._run_tool(tool_name, repo_path)
            if result:
                results[tool_name] = result

        # Security tools (always try)
        semgrep_result = self._run_tool("semgrep", repo_path)
        if semgrep_result:
            results["semgrep"] = semgrep_result

        return results

    def _run_tool(self, tool_name: str, repo_path: Path, **kwargs) -> ToolResult | None:
        """Run a tool if registered."""
        if not self.tool_registry.is_registered(tool_name):
            return None
        return self.tool_registry.get(tool_name).run(repo_path, **kwargs)
