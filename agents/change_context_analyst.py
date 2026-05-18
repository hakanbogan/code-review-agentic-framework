"""Change and Context Analyst agent."""

from typing import List

from crewai import Agent, Crew, Task

from agents.base import BaseAgent
from app.config import Settings
from app.logging import get_logger
from domain import AgentDecision, AgentRole, FindingType, PRContext

logger = get_logger(__name__)


class ChangeContextAnalyst(BaseAgent):
    """Analyzes PR changes for consistency and context."""

    def __init__(self, settings: Settings):
        super().__init__(AgentRole.CHANGE_CONTEXT_ANALYST, settings)

    def analyze(self, context: PRContext) -> AgentDecision:
        """Analyze change context and consistency."""
        logger.info("Change Context Analyst starting analysis", extra={"pr_id": context.pr_metadata.pr_id})

        prompt_template = self.load_prompt()
        analysis_context = self._build_analysis_context(context, prompt_template)

        crew_agent = Agent(
            role="Change & Context Analyst",
            goal="Analyze PR changes for consistency and appropriate context",
            backstory="You are an expert at understanding code changes and ensuring they align with stated intentions.",
            llm=self.llm,
            verbose=False,
        )

        task = Task(
            description=analysis_context,
            agent=crew_agent,
            expected_output="JSON with findings array and reasoning string.",
        )

        result, elapsed = self._execute_with_timing(self._execute_task, crew_agent, task)

        # Parse LLM output to findings
        parsed = self._parse_llm_json_output(result.get("raw_output", ""))
        findings = self._parse_findings_from_llm(parsed, FindingType.CONSISTENCY, "change_analysis")
        validated = self._validate_findings(findings)

        logger.info(f"Change Context Analyst completed: {len(validated)} findings")

        return self._create_decision(
            task_description="Analyze PR changes for consistency and context",
            findings=validated,
            reasoning=parsed.get("reasoning", result.get("reasoning", "Analysis completed")),
            llm_calls=1,
            tokens_used=result.get("tokens", 0),
            execution_time=elapsed,
        )

    def _build_analysis_context(self, context: PRContext, prompt_template: str) -> str:
        """Build context string for analysis."""
        pr = context.pr_metadata
        pr_context = "\n".join([
            f"PR Title: {pr.title}",
            f"PR Description: {pr.description or 'No description'}",
            f"Commit Messages: {', '.join(pr.commit_messages)}",
            f"Files Changed: {pr.files_changed}",
            f"Lines Added: {pr.lines_added}, Lines Deleted: {pr.lines_deleted}",
            f"\nDiff:\n{context.diff_content[:8000]}",
        ])

        if "{pr_context}" in prompt_template:
            return prompt_template.replace("{pr_context}", pr_context)
        return f"{prompt_template}\n\n{pr_context}"

    def _execute_task(self, agent: Agent, task: Task) -> dict:
        """Execute CrewAI task and extract results."""
        try:
            crew = Crew(agents=[agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            output = str(result) if result else ""
            tokens = self._extract_tokens(result)
            return {
                "reasoning": output[:500] or "Analysis completed",
                "tokens": tokens,
                "raw_output": output,
            }
        except Exception as e:
            logger.error(f"Error executing CrewAI task: {e}")
            return {"reasoning": f"Analysis error: {e}", "tokens": 0, "raw_output": ""}
