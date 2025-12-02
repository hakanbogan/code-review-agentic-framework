"""Style and Format Reviewer agent."""

import json
from typing import List

from agents.base import BaseAgent
from app.config import Settings
from app.logging import get_logger
from domain import AgentDecision, AgentRole, Evidence, Finding, FindingType, PRContext, Severity

logger = get_logger(__name__)


class StyleFormatReviewer(BaseAgent):
    """Reviews code style and formatting issues."""

    def __init__(self, settings: Settings):
        super().__init__(AgentRole.STYLE_FORMATTER_REVIEWER, settings)
        self.max_nits = settings.max_nits_per_review

    def analyze(self, context: PRContext) -> AgentDecision:
        """Analyze style and format issues."""
        logger.info("Style & Format Reviewer starting analysis", extra={"pr_id": context.pr_metadata.pr_id})

        findings = []

        if "ruff" in context.tool_results:
            findings.extend(self._parse_ruff(context.tool_results["ruff"]))

        if "eslint" in context.tool_results:
            findings.extend(self._parse_eslint(context.tool_results["eslint"]))

        findings = self._apply_nit_limit(findings, self.max_nits)
        validated = self._validate_findings(findings)

        logger.info(f"Style & Format Reviewer completed: {len(validated)} findings")

        return self._create_decision(
            task_description="Review code style and formatting",
            findings=validated,
            reasoning="Analyzed linter output and applied nit limits",
            llm_calls=0,
            tokens_used=0,
            execution_time=0.0,
        )

    def _parse_ruff(self, tool_result) -> List[Finding]:
        """Parse ruff linter results into findings."""
        if not tool_result.success or not tool_result.output:
            return []

        findings = []
        try:
            violations = json.loads(tool_result.output)
            if not isinstance(violations, list):
                violations = violations.get("violations", [])

            for v in violations:
                if not isinstance(v, dict):
                    continue

                location = v.get("location", {})
                row = location.get("row", 0) if isinstance(location, dict) else 0

                filename = v.get("filename", "unknown")
                if "/" in str(filename):
                    filename = str(filename).split("/")[-1]

                # Extract patch if available
                fix = v.get("fix")
                patch = None
                if isinstance(fix, dict):
                    edits = fix.get("edits", [])
                    if edits:
                        patch = "\n".join(
                            str(e.get("content", "")) if isinstance(e, dict) else str(e) for e in edits if e
                        )
                elif isinstance(fix, str):
                    patch = fix

                findings.append(Finding(
                    type=FindingType.STYLE,
                    severity=Severity.NIT,
                    source_agent=self.role,
                    evidence=Evidence(
                        tool="ruff",
                        reference=f"{filename}:{row}",
                        snippet="",
                        metadata={"code": v.get("code"), "url": v.get("url")},
                    ),
                    title=f"[{v.get('code', '')}] Style violation",
                    description=v.get("message", ""),
                    location=f"{filename}:{row}",
                    has_patch=patch is not None,
                    patch=patch,
                ))
        except json.JSONDecodeError:
            logger.error("Failed to parse ruff output")

        return findings

    def _parse_eslint(self, tool_result) -> List[Finding]:
        """Parse eslint results into findings."""
        if not tool_result.success or not tool_result.output:
            return []

        findings = []
        try:
            data = json.loads(tool_result.output)
            for file_result in data.get("files", []):
                filename = file_result.get("filename", "")
                for msg in file_result.get("messages", []):
                    findings.append(Finding(
                        type=FindingType.STYLE,
                        severity=Severity.MINOR if msg.get("severity") == 2 else Severity.NIT,
                        source_agent=self.role,
                        evidence=Evidence(
                            tool="eslint",
                            reference=f"{filename}:{msg.get('line', 0)}",
                            snippet="",
                            metadata={"rule_id": msg.get("rule_id")},
                        ),
                        title=f"[{msg.get('rule_id', '')}] Style violation",
                        description=msg.get("message", ""),
                        location=f"{filename}:{msg.get('line', 0)}",
                    ))
        except json.JSONDecodeError:
            logger.error("Failed to parse eslint output")

        return findings
