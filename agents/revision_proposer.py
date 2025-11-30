"""Revision Proposer agent."""

from typing import List

from crewai import Agent, Task
from langchain_openai import ChatOpenAI

from agents.base import BaseAgent
from app.config import Settings
from domain import AgentDecision, AgentRole, Finding, PRContext
from app.logging import get_logger

logger = get_logger(__name__)


class RevisionProposer(BaseAgent):
    """Proposes code revisions based on other agents' findings."""

    def __init__(self, settings: Settings, upstream_decisions: List[AgentDecision]):
        super().__init__(AgentRole.REVISION_PROPOSER, settings)
        self.upstream_decisions = upstream_decisions
        self.max_patch_lines = settings.max_patch_lines
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            seed=settings.openai_seed,
        )

    def analyze(self, context: PRContext) -> AgentDecision:
        """Propose revisions based on upstream findings.

        Args:
            context: Complete PR context

        Returns:
            AgentDecision with revision proposals
        """
        logger.info(
            "Revision Proposer starting analysis",
            extra={"pr_id": context.pr_metadata.pr_id}
        )

        # Collect all upstream findings that need fixes
        upstream_findings = self._collect_upstream_findings()

        # Filter findings that don't already have patches
        findings_needing_patches = [
            f for f in upstream_findings
            if not f.has_patch and f.severity.value in ["major", "critical"]
        ]

        # Generate patches for high-priority findings
        findings_with_patches, elapsed, tokens = self._generate_patches(
            context,
            findings_needing_patches
        )

        validated_findings = self._validate_findings(findings_with_patches)

        logger.info(
            f"Revision Proposer completed: {len(validated_findings)} patches",
            extra={"pr_id": context.pr_metadata.pr_id}
        )

        return self._create_decision(
            task_description="Generate code revision proposals",
            findings=validated_findings,
            reasoning="Analyzed high-priority findings and generated patches",
            llm_calls=len(findings_needing_patches),
            tokens_used=tokens,
            execution_time=elapsed,
        )

    def _collect_upstream_findings(self) -> List[Finding]:
        """Collect all findings from upstream agents."""
        findings = []
        for decision in self.upstream_decisions:
            findings.extend(decision.findings)
        return findings

    def _generate_patches(
        self,
        context: PRContext,
        findings: List[Finding]
    ) -> tuple[List[Finding], float, int]:
        """Generate patches for findings.

        Args:
            context: PR context
            findings: Findings that need patches

        Returns:
            Tuple of (findings with patches, execution time, tokens used)
        """
        # Placeholder for actual patch generation
        # Would use CrewAI agent to generate patches

        findings_with_patches = []
        total_time = 0.0
        total_tokens = 0

        for finding in findings[:5]:  # Limit number of patches
            # Generate patch using LLM
            # For now, just mark as having a patch
            finding.has_patch = True
            finding.patch = "# Placeholder patch\n# Would contain actual fix"
            findings_with_patches.append(finding)

        return findings_with_patches, total_time, total_tokens
