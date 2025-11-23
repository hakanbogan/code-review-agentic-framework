"""Security analysis tools: Semgrep and Bandit."""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict

from domain import ToolResult
from tools.base import BaseTool


class SemgrepTool(BaseTool):
    """Semgrep for security vulnerability detection."""

    def __init__(self, semgrep_path: str = "semgrep"):
        super().__init__(name="semgrep", executable_path=semgrep_path)

    def run(
        self,
        target_path: Path,
        config: str = "auto",
        **kwargs: Any
    ) -> ToolResult:
        """Run semgrep on target.

        Args:
            target_path: Path to analyze
            config: Semgrep config/ruleset (default: "auto")
            **kwargs: Additional arguments

        Returns:
            ToolResult with security findings
        """
        self.validate_target(target_path)

        try:
            result, elapsed = self._execute_with_timing(
                self._run_semgrep,
                target_path,
                config
            )

            findings = self.parse_output(result)

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=result,
                execution_time_s=elapsed,
                metadata={
                    "finding_count": len(findings.get("results", [])),
                    "severity_breakdown": self._count_by_severity(findings),
                },
            )
        except subprocess.CalledProcessError as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                errors=[f"Semgrep failed: {e.stderr}"],
                execution_time_s=0.0,
            )

    def _run_semgrep(self, target_path: Path, config: str) -> str:
        """Execute semgrep command."""
        cmd = [
            self.executable_path,
            "scan",
            "--config", config,
            "--json",
            str(target_path),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse semgrep JSON output."""
        try:
            data = json.loads(output)
            results = data.get("results", [])

            return {
                "results": [
                    {
                        "check_id": r.get("check_id", ""),
                        "path": r.get("path", ""),
                        "start": r.get("start", {}),
                        "end": r.get("end", {}),
                        "message": r.get("extra", {}).get("message", ""),
                        "severity": r.get("extra", {}).get("severity", ""),
                        "metadata": r.get("extra", {}).get("metadata", {}),
                        "fix": r.get("extra", {}).get("fix"),
                    }
                    for r in results
                ]
            }
        except json.JSONDecodeError:
            return {"results": [], "parse_error": "Invalid JSON output"}

    def _count_by_severity(self, findings: Dict[str, Any]) -> Dict[str, int]:
        """Count findings by severity."""
        counts: Dict[str, int] = {}
        for result in findings.get("results", []):
            severity = result.get("severity", "unknown")
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def is_available(self) -> bool:
        """Check if semgrep is available."""
        try:
            subprocess.run(
                [self.executable_path, "--version"],
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


class BanditTool(BaseTool):
    """Bandit for Python security analysis."""

    def __init__(self, bandit_path: str = "bandit"):
        super().__init__(name="bandit", executable_path=bandit_path)

    def run(self, target_path: Path, **kwargs: Any) -> ToolResult:
        """Run bandit on target.

        Args:
            target_path: Path to analyze
            **kwargs: Additional arguments

        Returns:
            ToolResult with security findings
        """
        self.validate_target(target_path)

        try:
            result, elapsed = self._execute_with_timing(
                self._run_bandit,
                target_path
            )

            findings = self.parse_output(result)

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=result,
                execution_time_s=elapsed,
                metadata={
                    "finding_count": len(findings.get("results", [])),
                    "severity_breakdown": self._count_by_severity(findings),
                },
            )
        except subprocess.CalledProcessError as e:
            if e.returncode == 1 and e.stdout:
                findings = self.parse_output(e.stdout)
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=e.stdout,
                    execution_time_s=0.0,
                    metadata={
                        "finding_count": len(findings.get("results", [])),
                        "severity_breakdown": self._count_by_severity(findings),
                    },
                )
            return ToolResult(
                tool_name=self.name,
                success=False,
                errors=[f"Bandit failed: {e.stderr}"],
                execution_time_s=0.0,
            )

    def _run_bandit(self, target_path: Path) -> str:
        """Execute bandit command."""
        cmd = [
            self.executable_path,
            "-r" if target_path.is_dir() else "",
            str(target_path),
            "-f", "json",
        ]
        cmd = [c for c in cmd if c]  # Remove empty strings

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse bandit JSON output."""
        try:
            data = json.loads(output)
            results = data.get("results", [])

            return {
                "results": [
                    {
                        "test_id": r.get("test_id", ""),
                        "test_name": r.get("test_name", ""),
                        "filename": r.get("filename", ""),
                        "line_number": r.get("line_number", 0),
                        "line_range": r.get("line_range", []),
                        "issue_severity": r.get("issue_severity", ""),
                        "issue_confidence": r.get("issue_confidence", ""),
                        "issue_text": r.get("issue_text", ""),
                        "code": r.get("code", ""),
                    }
                    for r in results
                ]
            }
        except json.JSONDecodeError:
            return {"results": [], "parse_error": "Invalid JSON output"}

    def _count_by_severity(self, findings: Dict[str, Any]) -> Dict[str, int]:
        """Count findings by severity."""
        counts: Dict[str, int] = {}
        for result in findings.get("results", []):
            severity = result.get("issue_severity", "unknown")
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def is_available(self) -> bool:
        """Check if bandit is available."""
        try:
            subprocess.run(
                [self.executable_path, "--version"],
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
