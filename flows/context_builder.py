"""Context builder for PR reviews."""

from pathlib import Path
from typing import Dict
from uuid import uuid4

from domain import PRContext, PRMetadata, ToolResult
from tools import ToolRegistry
from app.logging import get_logger

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
        """Build complete PR context.

        Args:
            pr_metadata: PR metadata
            repo_path: Path to repository
            base_ref: Base git reference
            compare_ref: Compare git reference

        Returns:
            Complete PRContext with tool results
        """
        correlation_id = uuid4()
        logger.info(
            f"Building context for PR {pr_metadata.pr_id}",
            extra={"correlation_id": str(correlation_id)}
        )

        # Extract git diff
        git_tool = self.tool_registry.get("git_diff")
        diff_result = git_tool.run(repo_path, base_ref=base_ref, compare_ref=compare_ref)

        if not diff_result.success:
            raise RuntimeError(f"Failed to extract git diff: {diff_result.errors}")

        diff_content = diff_result.output or ""

        # Run analysis tools based on language
        tool_results: Dict[str, ToolResult] = {
            "git_diff": diff_result,
        }

        if pr_metadata.language == "python":
            tool_results.update(self._run_python_tools(repo_path))
        elif pr_metadata.language in ["javascript", "typescript"]:
            tool_results.update(self._run_js_tools(repo_path))

        # Always try to run security tools
        tool_results.update(self._run_security_tools(repo_path))

        logger.info(
            f"Context built with {len(tool_results)} tool results",
            extra={"correlation_id": str(correlation_id)}
        )

        return PRContext(
            correlation_id=correlation_id,
            pr_metadata=pr_metadata,
            diff_content=diff_content,
            tool_results=tool_results,
        )

    def _run_python_tools(self, repo_path: Path) -> Dict[str, ToolResult]:
        """Run Python-specific tools."""
        results = {}

        if self.tool_registry.is_registered("ruff"):
            ruff_tool = self.tool_registry.get("ruff")
            results["ruff"] = ruff_tool.run(repo_path)

        if self.tool_registry.is_registered("bandit"):
            bandit_tool = self.tool_registry.get("bandit")
            results["bandit"] = bandit_tool.run(repo_path)

        return results

    def _run_js_tools(self, repo_path: Path) -> Dict[str, ToolResult]:
        """Run JavaScript/TypeScript-specific tools."""
        results = {}

        if self.tool_registry.is_registered("eslint"):
            eslint_tool = self.tool_registry.get("eslint")
            results["eslint"] = eslint_tool.run(repo_path)

        return results

    def _run_security_tools(self, repo_path: Path) -> Dict[str, ToolResult]:
        """Run security analysis tools."""
        results = {}

        if self.tool_registry.is_registered("semgrep"):
            semgrep_tool = self.tool_registry.get("semgrep")
            results["semgrep"] = semgrep_tool.run(repo_path)

        return results
