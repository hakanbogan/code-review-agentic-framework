"""Review flow orchestration."""

from pathlib import Path
from time import time
from typing import List

from agents import (
    ChangeContextAnalyst,
    DocumentationReviewer,
    LogicBugReviewer,
    PerformanceReviewer,
    RevisionProposer,
    SecurityReviewer,
    StyleFormatReviewer,
    Supervisor,
    TestCoverageReviewer,
)
from app.config import Settings
from app.logging import LogContext, get_logger
from domain import AgentDecision, Finding, PRContext, PRMetadata, PRReviewResult, Severity, SystemType
from flows.context_builder import ContextBuilder
from tools.factory import create_tool_registry

logger = get_logger(__name__)


class ReviewFlow:
    """Orchestrates the multi-agent review process."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.tool_registry = create_tool_registry(settings)
        self.context_builder = ContextBuilder(self.tool_registry)

    def run_single_agent_review(self, pr_metadata: PRMetadata, repo_path: Path) -> PRReviewResult:
        """Run single-agent review (baseline)."""
        start_time = time()
        context = self.context_builder.build_context(pr_metadata, repo_path)

        with LogContext(correlation_id=context.correlation_id):
            logger.info("Starting single-agent review")

            decision = ChangeContextAnalyst(self.settings).analyze(context)
            result = self._synthesize_review(context, [decision], SystemType.SINGLE_AGENT, time() - start_time)

            logger.info(f"Single-agent review completed: {len(result.findings)} findings")
            return result

    def run_multi_agent_review(self, pr_metadata: PRMetadata, repo_path: Path) -> PRReviewResult:
        """Run multi-agent review (proposed system)."""
        start_time = time()
        context = self.context_builder.build_context(pr_metadata, repo_path)

        with LogContext(correlation_id=context.correlation_id):
            logger.info("Starting multi-agent review")

            # Phase 1: Analysis agents
            parallel_decisions = self._run_analysis_agents(context)

            # Phase 2: Revision proposer
            revision_decision = RevisionProposer(self.settings, parallel_decisions).analyze(context)

            # Phase 3: Supervisor consolidation
            all_decisions = parallel_decisions + [revision_decision]
            supervisor_decision = Supervisor(self.settings, all_decisions).analyze(context)

            result = self._synthesize_review(
                context, all_decisions + [supervisor_decision], SystemType.MULTI_AGENT, time() - start_time
            )

            logger.info(f"Multi-agent review completed: {len(result.findings)} findings")
            return result

    def _run_analysis_agents(self, context: PRContext) -> List[AgentDecision]:
        """Run analysis agents."""
        logger.info("Running analysis agents")

        agents = [
            ChangeContextAnalyst(self.settings),
            SecurityReviewer(self.settings),
            StyleFormatReviewer(self.settings),
            LogicBugReviewer(self.settings),
            PerformanceReviewer(self.settings),
            DocumentationReviewer(self.settings),
            TestCoverageReviewer(self.settings),
        ]

        decisions = []
        for agent in agents:
            try:
                decision = agent.analyze(context)
                decisions.append(decision)
            except Exception as e:
                logger.error(f"Agent {agent.role.value} failed: {e}")
                continue

        return decisions

    def _synthesize_review(
        self, context: PRContext, decisions: List[AgentDecision], system_type: SystemType, total_time: float
    ) -> PRReviewResult:
        """Synthesize final review from agent decisions."""
        final_findings = decisions[-1].findings if decisions else []
        change_summary = self._generate_summary(context, final_findings)
        final_comment = self._generate_markdown(context, final_findings, change_summary)

        total_tokens = sum(d.tokens_used for d in decisions)

        return PRReviewResult(
            correlation_id=context.correlation_id,
            pr_id=context.pr_metadata.pr_id,
            system_type=system_type,
            change_summary=change_summary,
            findings=final_findings,
            agent_decisions=decisions,
            final_comment_md=final_comment,
            review_time_s=total_time,
            token_cost_estimate=self._estimate_cost(total_tokens),
            prompt_versions={d.agent_role.value: d.prompt_version for d in decisions},
        )

    def _generate_summary(self, context: PRContext, findings: List[Finding]) -> str:
        """Generate high-level change summary."""
        pr = context.pr_metadata
        return (
            f"Reviewed PR #{pr.pr_id}: {pr.title}\n"
            f"Changed {pr.files_changed} files (+{pr.lines_added}/-{pr.lines_deleted})\n"
            f"Found {len(findings)} issues requiring attention."
        )

    def _generate_markdown(self, context: PRContext, findings: List[Finding], summary: str) -> str:
        """Generate final markdown review comment."""
        lines = ["# Code Review", "", "## Summary", summary, ""]

        severity_config = [
            (Severity.CRITICAL, "🔴 Critical Issues"),
            (Severity.MAJOR, "🟠 Major Issues"),
            (Severity.MINOR, "🟡 Minor Issues"),
            (Severity.NIT, "💬 Nits"),
        ]

        by_severity = {}
        for f in findings:
            by_severity.setdefault(f.severity, []).append(f)

        for severity, header in severity_config:
            if severity in by_severity:
                lines.extend([f"## {header}", ""])
                for f in by_severity[severity]:
                    lines.extend(self._format_finding(f))
                lines.append("")

        return "\n".join(lines)

    def _format_finding(self, f: Finding) -> List[str]:
        """Format a single finding as markdown."""
        lines = [
            f"### {f.title}",
            "",
            f"**Location:** `{f.location}`  ",
            f"**Type:** {f.type.value}  ",
            f"**Source:** {f.evidence.tool}  ",
            "",
            f.description,
            "",
        ]

        if f.has_patch and f.patch:
            lines.extend(["**Suggested fix:**", "```", f.patch, "```", ""])

        return lines

    def _estimate_cost(self, total_tokens: int) -> float:
        """Estimate cost in USD (GPT-4-turbo pricing, 70/30 input/output split)."""
        input_tokens = int(total_tokens * 0.7)
        output_tokens = int(total_tokens * 0.3)
        return round((input_tokens / 1000 * 0.01) + (output_tokens / 1000 * 0.03), 4)
