"""Git diff extraction tool."""

import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from domain import ToolResult
from tools.base import BaseTool


class GitDiffTool(BaseTool):
    """Extract git diff for analysis."""

    def __init__(self, git_path: str = "git"):
        super().__init__(name="git_diff", executable_path=git_path)

    def run(
        self,
        target_path: Path,
        base_ref: str = "HEAD",
        compare_ref: Optional[str] = None,
        **kwargs: Any
    ) -> ToolResult:
        """Extract git diff.

        Args:
            target_path: Repository path
            base_ref: Base reference (default: HEAD)
            compare_ref: Reference to compare against (default: working tree)

        Returns:
            ToolResult with diff content
        """
        self.validate_target(target_path)

        if not self._is_git_repo(target_path):
            return ToolResult(
                tool_name=self.name,
                success=False,
                errors=["Not a git repository"],
                execution_time_s=0.0,
            )

        try:
            result, elapsed = self._execute_with_timing(
                self._extract_diff,
                target_path,
                base_ref,
                compare_ref
            )

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=result["diff"],
                execution_time_s=elapsed,
                metadata={
                    "base_ref": base_ref,
                    "compare_ref": compare_ref or "working_tree",
                    "files_changed": result["files_changed"],
                    "insertions": result["insertions"],
                    "deletions": result["deletions"],
                },
            )
        except subprocess.CalledProcessError as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                errors=[f"Git command failed: {e.stderr}"],
                execution_time_s=0.0,
            )

    def _extract_diff(
        self,
        repo_path: Path,
        base_ref: str,
        compare_ref: Optional[str]
    ) -> Dict[str, Any]:
        """Extract diff and statistics."""
        # Get diff
        diff_cmd = [self.executable_path, "diff", base_ref]
        if compare_ref:
            diff_cmd.append(compare_ref)

        diff_result = subprocess.run(
            diff_cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

        # Get statistics
        stat_cmd = [self.executable_path, "diff", "--numstat", base_ref]
        if compare_ref:
            stat_cmd.append(compare_ref)

        stat_result = subprocess.run(
            stat_cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

        files_changed, insertions, deletions = self._parse_stat(stat_result.stdout)

        return {
            "diff": diff_result.stdout,
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
        }

    def _parse_stat(self, stat_output: str) -> tuple[int, int, int]:
        """Parse git diff --numstat output."""
        files_changed = 0
        insertions = 0
        deletions = 0

        for line in stat_output.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                files_changed += 1
                try:
                    insertions += int(parts[0]) if parts[0] != "-" else 0
                    deletions += int(parts[1]) if parts[1] != "-" else 0
                except ValueError:
                    pass

        return files_changed, insertions, deletions

    def _is_git_repo(self, path: Path) -> bool:
        """Check if path is a git repository."""
        try:
            subprocess.run(
                [self.executable_path, "rev-parse", "--git-dir"],
                cwd=path,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse diff output (already structured by run method)."""
        return {"diff": output}

    def is_available(self) -> bool:
        """Check if git is available."""
        try:
            subprocess.run(
                [self.executable_path, "--version"],
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
