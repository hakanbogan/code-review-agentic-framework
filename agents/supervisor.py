"""Supervisor/QA-Checker agent."""

from typing import Dict, List

from crewai import Agent
from langchain_openai import ChatOpenAI

from agents.base import BaseAgent
from app.config import Settings
from domain import AgentDecision, AgentRole, Finding, FindingType, PRContext, Severity
from app.logging import get_logger

logger = get_logger(__name__)


class Supervisor(BaseAgent):
    """Supervises and consolidates findings from all agents."""

    def __init__(self, settings: Settings, agent_decisions: List[AgentDecision]):
        super().__init__(AgentRole.SUPERVISOR, settings)
        self.agent_decisions = agent_decisions
        self.max_nits = settings.max_nits_per_review
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            model_kwargs={"seed": settings.openai_seed},
        )

    def analyze(self, context: PRContext) -> AgentDecision:
        """Consolidate and validate findings from all agents.

        Args:
            context: Complete PR context

        Returns:
            AgentDecision with consolidated findings
        """
        logger.info(
            "Supervisor starting consolidation",
            extra={"pr_id": context.pr_metadata.pr_id}
        )

        # Collect all findings
        all_findings = []
        for decision in self.agent_decisions:
            all_findings.extend(decision.findings)

        # Remove duplicates
        findings = self._deduplicate_findings(all_findings)

        # Resolve conflicts (prioritize security)
        findings = self._resolve_conflicts(findings)

        # Apply nit limit
        findings = self._apply_nit_limit(findings)

        # Ensure all findings have evidence
        findings = self._validate_findings(findings)

        logger.info(
            f"Supervisor completed: {len(findings)} final findings",
            extra={"pr_id": context.pr_metadata.pr_id}
        )

        return self._create_decision(
            task_description="Consolidate and validate all findings",
            findings=findings,
            reasoning=(
                f"Consolidated {len(all_findings)} findings from {len(self.agent_decisions)} agents. "
                f"Applied deduplication, conflict resolution, and evidence validation."
            ),
            llm_calls=0,
            tokens_used=0,
            execution_time=0.0,
        )

    def _deduplicate_findings(self, findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings based on location and type."""
        seen: Dict[str, Finding] = {}

        for finding in findings:
            # Create key from location and type
            key = f"{finding.location}:{finding.type.value}"

            if key not in seen:
                seen[key] = finding
            else:
                # If duplicate, keep the one with higher severity
                existing = seen[key]
                if self._severity_rank(finding.severity) > self._severity_rank(existing.severity):
                    seen[key] = finding

        deduped = list(seen.values())
        logger.info(
            f"Deduplicated findings: {len(findings)} -> {len(deduped)}",
        )
        return deduped

    def _resolve_conflicts(self, findings: List[Finding]) -> List[Finding]:
        """Resolve conflicting findings at the same location.

        Priority order: Security > Logic > Performance > Style
        """
        location_groups: Dict[str, List[Finding]] = {}

        # Group by location
        for finding in findings:
            if finding.location not in location_groups:
                location_groups[finding.location] = []
            location_groups[finding.location].append(finding)

        resolved = []
        for location, group in location_groups.items():
            if len(group) == 1:
                resolved.append(group[0])
            else:
                # Multiple findings at same location - prioritize
                prioritized = sorted(
                    group,
                    key=lambda f: (
                        self._type_priority(f.type),
                        self._severity_rank(f.severity)
                    ),
                    reverse=True
                )
                # Keep top 2 if both high priority, otherwise just top 1
                if len(prioritized) > 1 and self._type_priority(prioritized[1].type) >= 3:
                    resolved.extend(prioritized[:2])
                else:
                    resolved.append(prioritized[0])

        logger.info(
            f"Resolved conflicts: {len(findings)} -> {len(resolved)}",
        )
        return resolved

    def _apply_nit_limit(self, findings: List[Finding]) -> List[Finding]:
        """Apply maximum nit limit across all findings."""
        nits = [f for f in findings if f.severity == Severity.NIT]
        others = [f for f in findings if f.severity != Severity.NIT]

        if len(nits) <= self.max_nits:
            return findings

        # Prioritize nits with patches
        nits_sorted = sorted(
            nits,
            key=lambda f: (f.has_patch, self._type_priority(f.type)),
            reverse=True
        )

        limited_nits = nits_sorted[:self.max_nits]

        logger.info(
            f"Applied nit limit: {len(nits)} -> {len(limited_nits)}",
        )

        return others + limited_nits

    @staticmethod
    def _severity_rank(severity: Severity) -> int:
        """Get numeric rank for severity."""
        ranks = {
            Severity.CRITICAL: 4,
            Severity.MAJOR: 3,
            Severity.MINOR: 2,
            Severity.NIT: 1,
        }
        return ranks.get(severity, 0)

    @staticmethod
    def _type_priority(finding_type: FindingType) -> int:
        """Get priority score for finding type."""
        priorities = {
            FindingType.SECURITY: 5,
            FindingType.LOGIC: 4,
            FindingType.PERFORMANCE: 3,
            FindingType.CONSISTENCY: 2,
            FindingType.STYLE: 1,
            FindingType.OTHER: 0,
        }
        return priorities.get(finding_type, 0)
