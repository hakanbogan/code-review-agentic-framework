"""Review flow orchestration."""

from pathlib import Path
from time import time
from typing import Dict, List

from agents import (
    ChangeContextAnalyst,
    RevisionProposer,
    SecurityReviewer,
    StyleFormatReviewer,
    Supervisor,
)
from app.config import Settings
from app.logging import LogContext, get_logger
from domain import AgentDecision, PRContext, PRMetadata, PRReviewResult, SystemType
from flows.context_builder import ContextBuilder
from tools.factory import create_tool_registry

logger = get_logger(__name__)


class ReviewFlow:
    """Orchestrates the multi-agent review process."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.tool_registry = create_tool_registry(settings)
        self.context_builder = ContextBuilder(self.tool_registry)

    def run_single_agent_review(
        self,
        pr_metadata: PRMetadata,
        repo_path: Path,
    ) -> PRReviewResult:
        """Run single-agent review (baseline).

        Args:
            pr_metadata: PR metadata
            repo_path: Path to repository

        Returns:
            PRReviewResult for single-agent system
        """
        start_time = time()

        # Build context
        context = self.context_builder.build_context(pr_metadata, repo_path)

        with LogContext(correlation_id=context.correlation_id):
            logger.info("Starting single-agent review")

            # Use only CCA agent for baseline
            cca_agent = ChangeContextAnalyst(self.settings)
            decision = cca_agent.analyze(context)

            # Synthesize review
            result = self._synthesize_review(
                context=context,
                agent_decisions=[decision],
                system_type=SystemType.SINGLE_AGENT,
                total_time=time() - start_time,
            )

            logger.info(
                f"Single-agent review completed: {len(result.findings)} findings"
            )

            return result

    def run_multi_agent_review(
        self,
        pr_metadata: PRMetadata,
        repo_path: Path,
    ) -> PRReviewResult:
        """Run multi-agent review (proposed system).

        Args:
            pr_metadata: PR metadata
            repo_path: Path to repository

        Returns:
            PRReviewResult for multi-agent system
        """
        start_time = time()

        # Build context
        context = self.context_builder.build_context(pr_metadata, repo_path)

        with LogContext(correlation_id=context.correlation_id):
            logger.info("Starting multi-agent review")

            # Phase 1: Parallel analysis agents
            parallel_decisions = self._run_parallel_agents(context)

            # Phase 2: Revision proposer
            revision_decision = self._run_revision_proposer(context, parallel_decisions)

            # Phase 3: Supervisor consolidation
            all_decisions = parallel_decisions + [revision_decision]
            supervisor_decision = self._run_supervisor(context, all_decisions)

            # Synthesize final review
            result = self._synthesize_review(
                context=context,
                agent_decisions=all_decisions + [supervisor_decision],
                system_type=SystemType.MULTI_AGENT,
                total_time=time() - start_time,
            )

            logger.info(
                f"Multi-agent review completed: {len(result.findings)} findings"
            )

            return result

    def _run_parallel_agents(self, context: PRContext) -> List[AgentDecision]:
        """Run analysis agents in parallel.

        Args:
            context: PR context

        Returns:
            List of agent decisions
        """
        decisions = []

        # Create agents
        cca = ChangeContextAnalyst(self.settings)
        security = SecurityReviewer(self.settings)
        style = StyleFormatReviewer(self.settings)

        if self.settings.enable_parallel_agents:
            # In production, use threading or async
            # For now, sequential execution
            logger.info("Running parallel agents (sequential for now)")
            decisions.append(cca.analyze(context))
            decisions.append(security.analyze(context))
            decisions.append(style.analyze(context))
        else:
            decisions.append(cca.analyze(context))
            decisions.append(security.analyze(context))
            decisions.append(style.analyze(context))

        return decisions

    def _run_revision_proposer(
        self,
        context: PRContext,
        upstream_decisions: List[AgentDecision],
    ) -> AgentDecision:
        """Run revision proposer agent.

        Args:
            context: PR context
            upstream_decisions: Decisions from upstream agents

        Returns:
            Revision proposer decision
        """
        logger.info("Running revision proposer")
        proposer = RevisionProposer(self.settings, upstream_decisions)
        return proposer.analyze(context)

    def _run_supervisor(
        self,
        context: PRContext,
        agent_decisions: List[AgentDecision],
    ) -> AgentDecision:
        """Run supervisor agent.

        Args:
            context: PR context
            agent_decisions: All agent decisions

        Returns:
            Supervisor decision with consolidated findings
        """
        logger.info("Running supervisor")
        supervisor = Supervisor(self.settings, agent_decisions)
        return supervisor.analyze(context)

    def _synthesize_review(
        self,
        context: PRContext,
        agent_decisions: List[AgentDecision],
        system_type: SystemType,
        total_time: float,
    ) -> PRReviewResult:
        """Synthesize final review from agent decisions.

        Args:
            context: PR context
            agent_decisions: All agent decisions
            system_type: Type of review system
            total_time: Total execution time

        Returns:
            Complete PRReviewResult
        """
        # Get final findings from supervisor (last decision)
        final_findings = agent_decisions[-1].findings if agent_decisions else []

        # Generate change summary
        change_summary = self._generate_change_summary(context, final_findings)

        # Generate markdown comment
        final_comment = self._generate_markdown_comment(
            context,
            final_findings,
            change_summary,
        )

        # Calculate costs
        total_tokens = sum(d.tokens_used for d in agent_decisions)
        token_cost = self._estimate_cost(total_tokens)

        # Collect prompt versions
        prompt_versions = {
            d.agent_role.value: d.prompt_version
            for d in agent_decisions
        }

        return PRReviewResult(
            correlation_id=context.correlation_id,
            pr_id=context.pr_metadata.pr_id,
            system_type=system_type,
            change_summary=change_summary,
            findings=final_findings,
            agent_decisions=agent_decisions,
            final_comment_md=final_comment,
            review_time_s=total_time,
            token_cost_estimate=token_cost,
            prompt_versions=prompt_versions,
        )

    def _generate_change_summary(
        self,
        context: PRContext,
        findings: List,
    ) -> str:
        """Generate high-level change summary."""
        pr = context.pr_metadata
        return (
            f"Reviewed PR #{pr.pr_id}: {pr.title}\n"
            f"Changed {pr.files_changed} files "
            f"(+{pr.lines_added}/-{pr.lines_deleted})\n"
            f"Found {len(findings)} issues requiring attention."
        )

    def _generate_markdown_comment(
        self,
        context: PRContext,
        findings: List,
        summary: str,
    ) -> str:
        """Generate final markdown review comment."""
        from domain import Severity

        lines = [
            "# Code Review",
            "",
            "## Summary",
            summary,
            "",
        ]

        # Group by severity
        by_severity = {}
        for finding in findings:
            sev = finding.severity
            if sev not in by_severity:
                by_severity[sev] = []
            by_severity[sev].append(finding)

        # Critical and Major
        if Severity.CRITICAL in by_severity:
            lines.append("## 🔴 Critical Issues")
            lines.append("")
            for f in by_severity[Severity.CRITICAL]:
                lines.extend(self._format_finding(f))
            lines.append("")

        if Severity.MAJOR in by_severity:
            lines.append("## 🟠 Major Issues")
            lines.append("")
            for f in by_severity[Severity.MAJOR]:
                lines.extend(self._format_finding(f))
            lines.append("")

        # Minor
        if Severity.MINOR in by_severity:
            lines.append("## 🟡 Minor Issues")
            lines.append("")
            for f in by_severity[Severity.MINOR]:
                lines.extend(self._format_finding(f))
            lines.append("")

        # Nits
        if Severity.NIT in by_severity:
            lines.append("## 💬 Nits")
            lines.append("")
            for f in by_severity[Severity.NIT]:
                lines.extend(self._format_finding(f))
            lines.append("")

        return "\n".join(lines)

    def _format_finding(self, finding) -> List[str]:
        """Format a single finding as markdown."""
        lines = [
            f"### {finding.title}",
            "",
            f"**Location:** `{finding.location}`  ",
            f"**Type:** {finding.type.value}  ",
            f"**Source:** {finding.evidence.tool}  ",
            "",
            finding.description,
            "",
        ]

        if finding.has_patch and finding.patch:
            lines.extend([
                "**Suggested fix:**",
                "```",
                finding.patch,
                "```",
                "",
            ])

        return lines

    def _estimate_cost(self, total_tokens: int) -> float:
        """Estimate cost in USD based on tokens.

        Using GPT-4-turbo pricing as reference:
        - Input: $0.01 per 1K tokens
        - Output: $0.03 per 1K tokens
        Assuming 70/30 split
        """
        input_tokens = int(total_tokens * 0.7)
        output_tokens = int(total_tokens * 0.3)

        cost = (input_tokens / 1000 * 0.01) + (output_tokens / 1000 * 0.03)
        return round(cost, 4)
