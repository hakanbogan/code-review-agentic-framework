"""Security Reviewer agent."""

import json
from typing import List

from agents.base import BaseAgent
from app.config import Settings
from app.logging import get_logger
from domain import AgentDecision, AgentRole, Evidence, Finding, FindingType, PRContext, Severity

logger = get_logger(__name__)


class SecurityReviewer(BaseAgent):
    """Reviews code for security vulnerabilities."""

    def __init__(self, settings: Settings):
        super().__init__(AgentRole.SECURITY_REVIEWER, settings)

    def analyze(self, context: PRContext) -> AgentDecision:
        """Analyze security aspects of changes."""
        logger.info("Security Reviewer starting analysis", extra={"pr_id": context.pr_metadata.pr_id})

        findings = []

        if "semgrep" in context.tool_results:
            findings.extend(self._parse_semgrep(context.tool_results["semgrep"]))

        if "bandit" in context.tool_results:
            findings.extend(self._parse_bandit(context.tool_results["bandit"]))

        validated = self._validate_findings(findings)

        logger.info(f"Security Reviewer completed: {len(validated)} findings")

        return self._create_decision(
            task_description="Review code for security vulnerabilities",
            findings=validated,
            reasoning="Analyzed security tools output",
            llm_calls=0,
            tokens_used=0,
            execution_time=0.0,
        )

    def _parse_semgrep(self, tool_result) -> List[Finding]:
        """Parse semgrep results into findings."""
        if not tool_result.success or not tool_result.output:
            return []

        findings = []
        try:
            data = json.loads(tool_result.output)
            for r in data.get("results", []):
                findings.append(Finding(
                    type=FindingType.SECURITY,
                    severity=self._map_semgrep_severity(r.get("severity", "INFO")),
                    source_agent=self.role,
                    evidence=Evidence(
                        tool="semgrep",
                        reference=f"{r['path']}:{r['start']['line']}",
                        snippet=r.get("extra", {}).get("lines", ""),
                        metadata=r.get("metadata", {}),
                    ),
                    title=r.get("check_id", "Security Issue"),
                    description=r.get("message", ""),
                    location=f"{r['path']}:{r['start']['line']}-{r['end']['line']}",
                ))
        except json.JSONDecodeError:
            logger.error("Failed to parse semgrep output")

        return findings

    def _parse_bandit(self, tool_result) -> List[Finding]:
        """Parse bandit results into findings."""
        if not tool_result.success or not tool_result.output:
            return []

        findings = []
        try:
            data = json.loads(tool_result.output)
            for r in data.get("results", []):
                findings.append(Finding(
                    type=FindingType.SECURITY,
                    severity=self._map_bandit_severity(r.get("issue_severity", "LOW"),
                                                       r.get("issue_confidence", "LOW")),
                    source_agent=self.role,
                    evidence=Evidence(
                        tool="bandit",
                        reference=f"{r['filename']}:{r['line_number']}",
                        snippet=r.get("code", ""),
                        metadata={"test_id": r.get("test_id"), "test_name": r.get("test_name")},
                    ),
                    title=r.get("test_name", "Security Issue"),
                    description=r.get("issue_text", ""),
                    location=f"{r['filename']}:{r['line_number']}",
                ))
        except json.JSONDecodeError:
            logger.error("Failed to parse bandit output")

        return findings

    def _map_semgrep_severity(self, severity: str) -> Severity:
        """Map semgrep severity to domain severity."""
        return {"ERROR": Severity.CRITICAL, "WARNING": Severity.MAJOR, "INFO": Severity.MINOR}.get(
            severity.upper(), Severity.MINOR
        )

    def _map_bandit_severity(self, issue_severity: str, confidence: str) -> Severity:
        """Map bandit severity+confidence to domain severity."""
        if issue_severity == "HIGH" and confidence == "HIGH":
            return Severity.CRITICAL
        if issue_severity == "HIGH" or confidence == "HIGH":
            return Severity.MAJOR
        if issue_severity == "MEDIUM":
            return Severity.MINOR
        return Severity.NIT
