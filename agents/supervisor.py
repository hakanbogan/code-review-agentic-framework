"""Supervisor/QA-Checker agent."""

from typing import Dict, List

from agents.base import BaseAgent
from app.config import Settings
from app.logging import get_logger
from domain import AgentDecision, AgentRole, Finding, FindingType, PRContext, Severity

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
        findings = self._filter_low_quality(findings)
        findings = self._filter_minor_issues(findings)
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

    def _filter_low_quality(self, findings: List[Finding]) -> List[Finding]:
        """Filter out low-quality findings to improve precision."""
        filtered = []
        
        for f in findings:
            # Calculate quality score
            quality_score = self._calculate_quality_score(f)
            
            # Keep if high quality or has patch (actionable)
            if quality_score >= 0.6 or f.has_patch:
                filtered.append(f)
            elif f.severity == Severity.CRITICAL or f.severity == Severity.MAJOR:
                # Always keep critical/major even if quality is lower
                filtered.append(f)
        
        logger.info(f"Filtered low quality: {len(findings)} -> {len(filtered)}")
        return filtered

    def _calculate_quality_score(self, finding: Finding) -> float:
        """Calculate quality score for a finding (0.0 to 1.0)."""
        score = 0.0
        
        # Base score from severity
        severity_scores = {
            Severity.CRITICAL: 1.0,
            Severity.MAJOR: 0.8,
            Severity.MINOR: 0.5,
            Severity.NIT: 0.3,
        }
        score += severity_scores.get(finding.severity, 0.0) * 0.4
        
        # Type priority boost
        type_scores = {
            FindingType.SECURITY: 1.0,
            FindingType.LOGIC: 0.9,
            FindingType.PERFORMANCE: 0.8,
            FindingType.CONSISTENCY: 0.6,
            FindingType.STYLE: 0.4,
            FindingType.OTHER: 0.3,
        }
        score += type_scores.get(finding.type, 0.0) * 0.3
        
        # Evidence quality (has location and description)
        if finding.location and finding.description:
            score += 0.2
        if finding.evidence and finding.evidence.snippet:
            score += 0.1
        
        return min(score, 1.0)

    def _filter_minor_issues(self, findings: List[Finding]) -> List[Finding]:
        """Aggressively filter minor issues to reduce noise."""
        filtered = []
        minor_count = 0
        max_minor = 3  # Limit minor findings
        
        # Separate by severity
        critical_major = [f for f in findings if f.severity in [Severity.CRITICAL, Severity.MAJOR]]
        minor_nit = [f for f in findings if f.severity in [Severity.MINOR, Severity.NIT]]
        
        # Keep all critical/major
        filtered.extend(critical_major)
        
        # Prioritize minor findings with patches or high type priority
        minor_sorted = sorted(
            minor_nit,
            key=lambda f: (f.has_patch, self.type_priority(f.type), f.severity == Severity.MINOR),
            reverse=True
        )
        
        # Keep top minor findings
        filtered.extend(minor_sorted[:max_minor])
        minor_count = len([f for f in filtered if f.severity == Severity.MINOR])
        
        logger.info(f"Filtered minor issues: {len(minor_nit)} -> {len(filtered) - len(critical_major)}")
        return filtered
