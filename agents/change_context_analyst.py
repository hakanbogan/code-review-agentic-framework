"""Change and Context Analyst agent."""

from typing import List

from crewai import Agent, Task
from langchain_openai import ChatOpenAI

from agents.base import BaseAgent
from app.config import Settings
from domain import AgentDecision, AgentRole, Evidence, Finding, FindingType, PRContext, Severity
from app.logging import get_logger

logger = get_logger(__name__)


class ChangeContextAnalyst(BaseAgent):
    """Analyzes PR changes for consistency and context."""

    def __init__(self, settings: Settings):
        super().__init__(AgentRole.CHANGE_CONTEXT_ANALYST, settings)
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            model_kwargs={"seed": settings.openai_seed},
        )

    def analyze(self, context: PRContext) -> AgentDecision:
        """Analyze change context and consistency.

        Args:
            context: Complete PR context

        Returns:
            AgentDecision with consistency findings
        """
        logger.info(
            "Change Context Analyst starting analysis",
            extra={"pr_id": context.pr_metadata.pr_id}
        )

        prompt_template = self.load_prompt()

        # Create CrewAI agent
        crew_agent = Agent(
            role="Change & Context Analyst",
            goal="Analyze PR changes for consistency and appropriate context",
            backstory=(
                "You are an expert at understanding code changes and ensuring they "
                "align with stated intentions and project context."
            ),
            llm=self.llm,
            verbose=True,
        )

        # Build analysis context
        analysis_context = self._build_analysis_context(context, prompt_template)

        # Create task
        task = Task(
            description=analysis_context,
            agent=crew_agent,
            expected_output="A structured analysis of change consistency and context issues.",
        )

        # Execute analysis
        result, elapsed = self._execute_with_timing(
            self._execute_task,
            crew_agent,
            task
        )

        # Parse findings
        findings = self._parse_findings(result, context)
        validated_findings = self._validate_findings(findings)

        logger.info(
            f"Change Context Analyst completed: {len(validated_findings)} findings",
            extra={"pr_id": context.pr_metadata.pr_id}
        )

        return self._create_decision(
            task_description="Analyze PR changes for consistency and context",
            findings=validated_findings,
            reasoning=result.get("reasoning", "Analysis completed"),
            llm_calls=1,
            tokens_used=result.get("tokens", 0),
            execution_time=elapsed,
        )

    def _build_analysis_context(self, context: PRContext, prompt_template: str) -> str:
        """Build context string for analysis."""
        pr = context.pr_metadata

        context_parts = [
            f"PR Title: {pr.title}",
            f"PR Description: {pr.description or 'No description'}",
            f"Commit Messages: {', '.join(pr.commit_messages)}",
            f"Files Changed: {pr.files_changed}",
            f"Lines Added: {pr.lines_added}, Lines Deleted: {pr.lines_deleted}",
            f"\nDiff:\n{context.diff_content[:5000]}",  # Limit diff size
        ]

        return prompt_template.format(
            pr_context="\n".join(context_parts)
        )

    def _execute_task(self, agent: Agent, task: Task) -> dict:
        """Execute CrewAI task and extract results."""
        # For now, simulate execution
        # In real implementation, use agent.execute_task(task)
        return {
            "reasoning": "Analyzed PR for consistency",
            "tokens": 500,
            "findings": [],
        }

    def _parse_findings(self, result: dict, context: PRContext) -> List[Finding]:
        """Parse agent output into structured findings."""
        findings = []

        # Extract findings from result
        # This is a placeholder - actual implementation would parse LLM output
        for finding_data in result.get("findings", []):
            finding = Finding(
                type=FindingType.CONSISTENCY,
                severity=Severity.MINOR,
                source_agent=self.role,
                evidence=Evidence(
                    tool="git_diff",
                    reference=finding_data.get("location", ""),
                    snippet=finding_data.get("snippet"),
                ),
                title=finding_data.get("title", ""),
                description=finding_data.get("description", ""),
                location=finding_data.get("location", ""),
            )
            findings.append(finding)

        return findings
