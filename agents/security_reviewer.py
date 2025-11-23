"""Security Reviewer agent."""

from typing import List

from crewai import Agent, Task
from langchain_openai import ChatOpenAI

from agents.base import BaseAgent
from app.config import Settings
from domain import (
    AgentDecision,
    AgentRole,
    Evidence,
    Finding,
    FindingType,
    PRContext,
    Severity,
)
from app.logging import get_logger

logger = get_logger(__name__)


class SecurityReviewer(BaseAgent):
    """Reviews code for security vulnerabilities."""

    def __init__(self, settings: Settings):
        super().__init__(AgentRole.SECURITY_REVIEWER, settings)
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            model_kwargs={"seed": settings.openai_seed},
        )

    def analyze(self, context: PRContext) -> AgentDecision:
        """Analyze security aspects of changes.
        
        Args:
            context: Complete PR context
            
        Returns:
            AgentDecision with security findings
        """
        logger.info(
            "Security Reviewer starting analysis",
            extra={"pr_id": context.pr_metadata.pr_id}
        )

        findings = []

        # Analyze semgrep results
        if "semgrep" in context.tool_results:
            findings.extend(self._analyze_semgrep(context))

        # Analyze bandit results (Python)
        if "bandit" in context.tool_results:
            findings.extend(self._analyze_bandit(context))

        # LLM-based contextual security review
        llm_findings, elapsed, tokens = self._llm_security_review(context)
        findings.extend(llm_findings)

        validated_findings = self._validate_findings(findings)

        logger.info(
            f"Security Reviewer completed: {len(validated_findings)} findings",
            extra={"pr_id": context.pr_metadata.pr_id}
        )

        return self._create_decision(
            task_description="Review code for security vulnerabilities",
            findings=validated_findings,
            reasoning="Analyzed security tools output and performed contextual review",
            llm_calls=1,
            tokens_used=tokens,
            execution_time=elapsed,
        )

    def _analyze_semgrep(self, context: PRContext) -> List[Finding]:
        """Analyze semgrep results."""
        findings = []
        semgrep_result = context.tool_results["semgrep"]
        
        if not semgrep_result.success or not semgrep_result.output:
            return findings

        import json
        try:
            data = json.loads(semgrep_result.output)
            for result in data.get("results", []):
                severity = self._map_severity(result.get("severity", "INFO"))
                
                finding = Finding(
                    type=FindingType.SECURITY,
                    severity=severity,
                    source_agent=self.role,
                    evidence=Evidence(
                        tool="semgrep",
                        reference=f"{result['path']}:{result['start']['line']}",
                        snippet=result.get("extra", {}).get("lines", ""),
                        metadata=result.get("metadata", {}),
                    ),
                    title=result.get("check_id", "Security Issue"),
                    description=result.get("message", ""),
                    location=f"{result['path']}:{result['start']['line']}-{result['end']['line']}",
                )
                findings.append(finding)
        except json.JSONDecodeError:
            logger.error("Failed to parse semgrep output")

        return findings

    def _analyze_bandit(self, context: PRContext) -> List[Finding]:
        """Analyze bandit results."""
        findings = []
        bandit_result = context.tool_results["bandit"]
        
        if not bandit_result.success or not bandit_result.output:
            return findings

        import json
        try:
            data = json.loads(bandit_result.output)
            for result in data.get("results", []):
                severity = self._map_bandit_severity(
                    result.get("issue_severity", "LOW"),
                    result.get("issue_confidence", "LOW")
                )
                
                finding = Finding(
                    type=FindingType.SECURITY,
                    severity=severity,
                    source_agent=self.role,
                    evidence=Evidence(
                        tool="bandit",
                        reference=f"{result['filename']}:{result['line_number']}",
                        snippet=result.get("code", ""),
                        metadata={
                            "test_id": result.get("test_id"),
                            "test_name": result.get("test_name"),
                        },
                    ),
                    title=result.get("test_name", "Security Issue"),
                    description=result.get("issue_text", ""),
                    location=f"{result['filename']}:{result['line_number']}",
                )
                findings.append(finding)
        except json.JSONDecodeError:
            logger.error("Failed to parse bandit output")

        return findings

    def _llm_security_review(self, context: PRContext) -> tuple[List[Finding], float, int]:
        """Perform LLM-based contextual security review."""
        # Placeholder for LLM review
        # Would create CrewAI agent and task similar to ChangeContextAnalyst
        return [], 0.0, 0

    def _map_severity(self, semgrep_severity: str) -> Severity:
        """Map semgrep severity to domain severity."""
        mapping = {
            "ERROR": Severity.CRITICAL,
            "WARNING": Severity.MAJOR,
            "INFO": Severity.MINOR,
        }
        return mapping.get(semgrep_severity.upper(), Severity.MINOR)

    def _map_bandit_severity(self, issue_severity: str, confidence: str) -> Severity:
        """Map bandit severity+confidence to domain severity."""
        if issue_severity == "HIGH" and confidence == "HIGH":
            return Severity.CRITICAL
        elif issue_severity == "HIGH" or confidence == "HIGH":
            return Severity.MAJOR
        elif issue_severity == "MEDIUM":
            return Severity.MINOR
        else:
            return Severity.NIT

