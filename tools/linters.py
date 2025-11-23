"""Ruff linter tool for Python code analysis."""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from domain import ToolResult
from tools.base import BaseTool


class RuffTool(BaseTool):
    """Ruff Python linter and formatter."""

    def __init__(self, ruff_path: str = "ruff"):
        super().__init__(name="ruff", executable_path=ruff_path)

    def run(self, target_path: Path, **kwargs: Any) -> ToolResult:
        """Run ruff on target.

        Args:
            target_path: Path to analyze
            **kwargs: Additional arguments (config_path, etc.)

        Returns:
            ToolResult with violations
        """
        self.validate_target(target_path)

        try:
            result, elapsed = self._execute_with_timing(
                self._run_ruff,
                target_path,
                kwargs.get("config_path")
            )

            violations = self.parse_output(result)

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=result,
                execution_time_s=elapsed,
                metadata={
                    "violation_count": len(violations.get("violations", [])),
                    "files_analyzed": len(set(v["filename"] for v in violations.get("violations", []))),
                },
            )
        except subprocess.CalledProcessError as e:
            # Ruff returns non-zero exit code when violations found
            if e.returncode == 1 and e.stdout:
                violations = self.parse_output(e.stdout)
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=e.stdout,
                    execution_time_s=0.0,
                    metadata={
                        "violation_count": len(violations.get("violations", [])),
                        "files_analyzed": len(set(v["filename"] for v in violations.get("violations", []))),
                    },
                )
            return ToolResult(
                tool_name=self.name,
                success=False,
                errors=[f"Ruff failed: {e.stderr}"],
                execution_time_s=0.0,
            )

    def _run_ruff(self, target_path: Path, config_path: Path | None) -> str:
        """Execute ruff command."""
        cmd = [
            self.executable_path,
            "check",
            str(target_path),
            "--output-format=json",
        ]

        if config_path:
            cmd.extend(["--config", str(config_path)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse ruff JSON output."""
        try:
            violations = json.loads(output)
            return {
                "violations": [
                    {
                        "filename": v.get("filename", ""),
                        "location": v.get("location", {}),
                        "end_location": v.get("end_location", {}),
                        "code": v.get("code", ""),
                        "message": v.get("message", ""),
                        "fix": v.get("fix"),
                        "url": v.get("url"),
                    }
                    for v in violations
                ]
            }
        except json.JSONDecodeError:
            return {"violations": [], "parse_error": "Invalid JSON output"}

    def is_available(self) -> bool:
        """Check if ruff is available."""
        try:
            subprocess.run(
                [self.executable_path, "--version"],
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


class ESLintTool(BaseTool):
    """ESLint for JavaScript/TypeScript analysis."""

    def __init__(self, eslint_path: str = "eslint"):
        super().__init__(name="eslint", executable_path=eslint_path)

    def run(self, target_path: Path, **kwargs: Any) -> ToolResult:
        """Run ESLint on target.

        Args:
            target_path: Path to analyze
            **kwargs: Additional arguments

        Returns:
            ToolResult with violations
        """
        self.validate_target(target_path)

        try:
            result, elapsed = self._execute_with_timing(
                self._run_eslint,
                target_path
            )

            violations = self.parse_output(result)

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=result,
                execution_time_s=elapsed,
                metadata={
                    "violation_count": sum(
                        len(f.get("messages", []))
                        for f in violations.get("files", [])
                    ),
                    "files_analyzed": len(violations.get("files", [])),
                },
            )
        except subprocess.CalledProcessError as e:
            if e.returncode == 1 and e.stdout:
                violations = self.parse_output(e.stdout)
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=e.stdout,
                    execution_time_s=0.0,
                    metadata={
                        "violation_count": sum(
                            len(f.get("messages", []))
                            for f in violations.get("files", [])
                        ),
                        "files_analyzed": len(violations.get("files", [])),
                    },
                )
            return ToolResult(
                tool_name=self.name,
                success=False,
                errors=[f"ESLint failed: {e.stderr}"],
                execution_time_s=0.0,
            )

    def _run_eslint(self, target_path: Path) -> str:
        """Execute ESLint command."""
        cmd = [
            self.executable_path,
            str(target_path),
            "--format=json",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse ESLint JSON output."""
        try:
            results = json.loads(output)
            return {
                "files": [
                    {
                        "filename": r.get("filePath", ""),
                        "messages": [
                            {
                                "line": m.get("line"),
                                "column": m.get("column"),
                                "severity": m.get("severity"),
                                "message": m.get("message"),
                                "rule_id": m.get("ruleId"),
                            }
                            for m in r.get("messages", [])
                        ],
                    }
                    for r in results
                ]
            }
        except json.JSONDecodeError:
            return {"files": [], "parse_error": "Invalid JSON output"}

    def is_available(self) -> bool:
        """Check if ESLint is available."""
        try:
            subprocess.run(
                [self.executable_path, "--version"],
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
