"""Logic and Bug Reviewer agent."""

from crewai import Agent, Crew, Task

from agents.base import BaseAgent
from app.config import Settings
from app.logging import get_logger
from domain import AgentDecision, AgentRole, FindingType, PRContext

logger = get_logger(__name__)


class LogicBugReviewer(BaseAgent):
    """Reviews code for logical errors and potential bugs."""

    def __init__(self, settings: Settings):
        super().__init__(AgentRole.LOGIC_REVIEWER, settings)

    def analyze(self, context: PRContext) -> AgentDecision:
        """Analyze code for logical errors and bugs."""
        logger.info("Logic Bug Reviewer starting analysis", extra={"pr_id": context.pr_metadata.pr_id})

        prompt_template = self.load_prompt()
        analysis_context = self._build_analysis_context(context, prompt_template)

        crew_agent = Agent(
            role="Logic & Bug Reviewer",
            goal="Identify logical errors, edge cases, and potential bugs in code changes",
            backstory=(
                "You are an expert software engineer specialized in finding subtle bugs, "
                "edge cases, and logical errors that could cause runtime failures or incorrect behavior."
            ),
            llm=self.llm,
            verbose=False,
        )

        task = Task(
            description=analysis_context,
            agent=crew_agent,
            expected_output="JSON with findings array containing logic/bug issues and reasoning string.",
        )

        result, elapsed = self._execute_with_timing(self._execute_task, crew_agent, task)

        # Parse LLM output to findings
        parsed = self._parse_llm_json_output(result.get("raw_output", ""))
        findings = self._parse_findings_from_llm(parsed, FindingType.LOGIC, "logic_analysis")
        validated = self._validate_findings(findings)

        logger.info(f"Logic Bug Reviewer completed: {len(validated)} findings")

        return self._create_decision(
            task_description="Review code for logical errors and potential bugs",
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
            f"Language: {pr.language}",
            f"Files Changed: {pr.files_changed}",
            f"\nCode Diff:\n{context.diff_content[:10000]}",
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
            return {
                "reasoning": output[:500] or "Analysis completed",
                "tokens": 0,
                "raw_output": output,
            }
        except Exception as e:
            logger.error(f"Error executing CrewAI task: {e}")
            return {"reasoning": f"Analysis error: {e}", "tokens": 0, "raw_output": ""}
