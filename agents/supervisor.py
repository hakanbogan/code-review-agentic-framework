"""Supervisor/QA-Checker agent."""

from typing import Dict, List

from agents.base import BaseAgent
from app.config import Settings
from app.logging import get_logger
from domain import AgentDecision, AgentRole, Finding, PRContext, Severity

logger = get_logger(__name__)


class Supervisor(BaseAgent):
    """Supervises and consolidates findings from all agents."""

    def __init__(self, settings: Settings, agent_decisions: List[AgentDecision]):
        super().__init__(AgentRole.SUPERVISOR, settings)
        self.agent_decisions = agent_decisions
        self.max_nits = settings.max_nits_per_review

    def analyze(self, context: PRContext) -> AgentDecision:
        """Consolidate and validate findings from all agents."""
        logger.info("Supervisor starting consolidation", extra={"pr_id": context.pr_metadata.pr_id})

        all_findings = [f for d in self.agent_decisions for f in d.findings]

        findings = self._deduplicate_findings(all_findings)
        findings = self._resolve_conflicts(findings)
        findings = self._apply_nit_limit(findings, self.max_nits)
        findings = self._validate_findings(findings)

        logger.info(f"Supervisor completed: {len(findings)} final findings")

        return self._create_decision(
            task_description="Consolidate and validate all findings",
            findings=findings,
            reasoning=f"Consolidated {len(all_findings)} findings from {len(self.agent_decisions)} agents.",
            llm_calls=0,
            tokens_used=0,
            execution_time=0.0,
        )

    def _deduplicate_findings(self, findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings based on location and type."""
        seen: Dict[str, Finding] = {}

        for f in findings:
            key = f"{f.location}:{f.type.value}"
            if key not in seen or self.severity_rank(f.severity) > self.severity_rank(seen[key].severity):
                seen[key] = f

        deduped = list(seen.values())
        logger.info(f"Deduplicated findings: {len(findings)} -> {len(deduped)}")
        return deduped

    def _resolve_conflicts(self, findings: List[Finding]) -> List[Finding]:
        """Resolve conflicting findings at the same location. Priority: Security > Logic > Performance > Style"""
        location_groups: Dict[str, List[Finding]] = {}

        for f in findings:
            location_groups.setdefault(f.location, []).append(f)

        resolved = []
        for group in location_groups.values():
            if len(group) == 1:
                resolved.append(group[0])
            else:
                prioritized = sorted(
                    group, key=lambda f: (self.type_priority(f.type), self.severity_rank(f.severity)), reverse=True
                )
                # Keep top 2 if both high priority
                if len(prioritized) > 1 and self.type_priority(prioritized[1].type) >= 3:
                    resolved.extend(prioritized[:2])
                else:
                    resolved.append(prioritized[0])

        logger.info(f"Resolved conflicts: {len(findings)} -> {len(resolved)}")
        return resolved
