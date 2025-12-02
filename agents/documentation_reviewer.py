"""Documentation Reviewer agent."""

from crewai import Agent, Crew, Task

from agents.base import BaseAgent
from app.config import Settings
from app.logging import get_logger
from domain import AgentDecision, AgentRole, FindingType, PRContext

logger = get_logger(__name__)


class DocumentationReviewer(BaseAgent):
    """Reviews code for documentation quality and completeness."""

    def __init__(self, settings: Settings):
        super().__init__(AgentRole.DOCUMENTATION_REVIEWER, settings)

    def analyze(self, context: PRContext) -> AgentDecision:
        """Analyze code for documentation issues."""
        logger.info("Documentation Reviewer starting analysis", extra={"pr_id": context.pr_metadata.pr_id})

        try:
            prompt_template = self.load_prompt()
        except FileNotFoundError:
            prompt_template = self._get_fallback_prompt()

        analysis_context = self._build_analysis_context(context, prompt_template)

        crew_agent = Agent(
            role="Documentation Reviewer",
            goal="Ensure code is well-documented with clear docstrings, comments, and type hints",
            backstory=(
                "You are a technical writer and code quality expert who ensures all code changes "
                "are properly documented with clear docstrings, meaningful comments, and complete type hints."
            ),
            llm=self.llm,
            verbose=False,
        )

        task = Task(
            description=analysis_context,
            agent=crew_agent,
            expected_output="JSON with findings array containing documentation issues and reasoning.",
        )

        result, elapsed = self._execute_with_timing(self._execute_task, crew_agent, task)

        parsed = self._parse_llm_json_output(result.get("raw_output", ""))
        findings = self._parse_findings_from_llm(parsed, FindingType.OTHER, "documentation_analysis")
        validated = self._validate_findings(findings)

        logger.info(f"Documentation Reviewer completed: {len(validated)} findings")

        return self._create_decision(
            task_description="Review code documentation quality",
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
        """Execute CrewAI task."""
        try:
            crew = Crew(agents=[agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            output = str(result) if result else ""
            return {"reasoning": output[:500], "tokens": 0, "raw_output": output}
        except Exception as e:
            logger.error(f"Error executing CrewAI task: {e}")
            return {"reasoning": f"Analysis error: {e}", "tokens": 0, "raw_output": ""}

    def _get_fallback_prompt(self) -> str:
        """Fallback prompt if file not found."""
        return """Review the code diff for documentation quality:

Check for:
- Missing or incomplete docstrings for functions/classes
- Missing type hints for function parameters and return values
- Outdated or misleading comments
- Complex code lacking explanatory comments
- Missing module-level documentation

{pr_context}

Return JSON with findings array. Each finding should have:
- type: "other" (for documentation)
- severity: "nit", "minor", "major"
- title: Brief description
- description: Detailed explanation
- location: File and line reference"""
