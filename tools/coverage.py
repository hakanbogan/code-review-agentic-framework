"""Coverage analysis tool."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

from domain import ToolResult
from tools.base import BaseTool


class CoverageReader(BaseTool):
    """Read and parse test coverage reports."""

    def __init__(self):
        super().__init__(name="coverage_reader", executable_path="")

    def run(self, target_path: Path, **kwargs: Any) -> ToolResult:
        """Read coverage report.

        Args:
            target_path: Path to coverage report (JSON or XML)
            **kwargs: Additional arguments

        Returns:
            ToolResult with coverage data
        """
        self.validate_target(target_path)

        try:
            if target_path.suffix == ".json":
                coverage_data = self._read_json_coverage(target_path)
            elif target_path.suffix == ".xml":
                coverage_data = self._read_xml_coverage(target_path)
            else:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    errors=[f"Unsupported coverage format: {target_path.suffix}"],
                    execution_time_s=0.0,
                )

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=json.dumps(coverage_data),
                execution_time_s=0.0,
                metadata={
                    "total_coverage": coverage_data.get("summary", {}).get("percent_covered", 0),
                    "files_analyzed": len(coverage_data.get("files", [])),
                },
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                errors=[f"Failed to read coverage: {str(e)}"],
                execution_time_s=0.0,
            )

    def _read_json_coverage(self, path: Path) -> Dict[str, Any]:
        """Read coverage.py JSON format."""
        with open(path) as f:
            data = json.load(f)

        files = []
        for filename, file_data in data.get("files", {}).items():
            summary = file_data.get("summary", {})
            files.append({
                "path": filename,
                "lines_covered": summary.get("covered_lines", 0),
                "lines_total": summary.get("num_statements", 0),
                "percent_covered": summary.get("percent_covered", 0),
                "missing_lines": file_data.get("missing_lines", []),
            })

        totals = data.get("totals", {})
        return {
            "summary": {
                "lines_covered": totals.get("covered_lines", 0),
                "lines_total": totals.get("num_statements", 0),
                "percent_covered": totals.get("percent_covered", 0),
            },
            "files": files,
        }

    def _read_xml_coverage(self, path: Path) -> Dict[str, Any]:
        """Read Cobertura XML format."""
        tree = ET.parse(path)
        root = tree.getroot()

        files = []
        for package in root.findall(".//package"):
            for cls in package.findall("classes/class"):
                filename = cls.get("filename", "")
                lines = cls.findall("lines/line")

                lines_total = len(lines)
                lines_covered = sum(1 for line in lines if int(line.get("hits", 0)) > 0)
                missing = [
                    int(line.get("number", 0))
                    for line in lines
                    if int(line.get("hits", 0)) == 0
                ]

                files.append({
                    "path": filename,
                    "lines_covered": lines_covered,
                    "lines_total": lines_total,
                    "percent_covered": (lines_covered / lines_total * 100) if lines_total > 0 else 0,
                    "missing_lines": missing,
                })

        # Calculate totals
        total_lines = sum(f["lines_total"] for f in files)
        covered_lines = sum(f["lines_covered"] for f in files)

        return {
            "summary": {
                "lines_covered": covered_lines,
                "lines_total": total_lines,
                "percent_covered": (covered_lines / total_lines * 100) if total_lines > 0 else 0,
            },
            "files": files,
        }

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse coverage data (already structured)."""
        return json.loads(output)

    def is_available(self) -> bool:
        """Coverage reader is always available."""
        return True
