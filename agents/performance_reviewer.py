"""Performance Reviewer agent."""

import ast
import re
from typing import List

from crewai import Agent, Crew, Task

from agents.base import BaseAgent
from app.config import Settings
from app.logging import get_logger
from domain import AgentDecision, AgentRole, Evidence, Finding, FindingType, PRContext, Severity

logger = get_logger(__name__)


class PerformanceReviewer(BaseAgent):
    """Reviews code for performance issues using hybrid approach (static + LLM)."""

    def __init__(self, settings: Settings):
        super().__init__(AgentRole.PERFORMANCE_REVIEWER, settings)

    def analyze(self, context: PRContext) -> AgentDecision:
        """Analyze code for performance issues."""
        logger.info("Performance Reviewer starting analysis", extra={"pr_id": context.pr_metadata.pr_id})

        findings = []

        # Phase 1: Static analysis for common patterns
        static_findings = self._static_analysis(context)
        findings.extend(static_findings)

        # Phase 2: LLM-based contextual analysis
        llm_findings, elapsed, tokens = self._llm_analysis(context)
        findings.extend(llm_findings)

        validated = self._validate_findings(findings)

        logger.info(f"Performance Reviewer completed: {len(validated)} findings")

        return self._create_decision(
            task_description="Review code for performance issues",
            findings=validated,
            reasoning=f"Static analysis: {len(static_findings)}, LLM analysis: {len(llm_findings)}",
            llm_calls=1,
            tokens_used=tokens,
            execution_time=elapsed,
        )

    def _static_analysis(self, context: PRContext) -> List[Finding]:
        """Perform static analysis for performance patterns."""
        findings = []
        diff_content = context.diff_content

        # Pattern 1: Nested loops (potential O(n^2))
        nested_loop_pattern = r"for\s+\w+\s+in\s+.+:\s*\n\s+for\s+\w+\s+in\s+"
        for match in re.finditer(nested_loop_pattern, diff_content):
            line_num = diff_content[:match.start()].count('\n') + 1
            findings.append(Finding(
                type=FindingType.PERFORMANCE,
                severity=Severity.MINOR,
                source_agent=self.role,
                evidence=Evidence(
                    tool="static_analysis",
                    reference=f"diff:line_{line_num}",
                    snippet=match.group()[:100],
                ),
                title="Nested loops detected - potential O(n²) complexity",
                description="Nested loops can lead to quadratic time complexity. Consider if this can be optimized.",
                location=f"diff:line_{line_num}",
            ))

        # Pattern 2: String concatenation in loop
        str_concat_pattern = r"for\s+\w+\s+in\s+.+:[\s\S]*?\+="
        for match in re.finditer(str_concat_pattern, diff_content):
            if "str" in match.group() or "'" in match.group() or '"' in match.group():
                line_num = diff_content[:match.start()].count('\n') + 1
                findings.append(Finding(
                    type=FindingType.PERFORMANCE,
                    severity=Severity.NIT,
                    source_agent=self.role,
                    evidence=Evidence(
                        tool="static_analysis",
                        reference=f"diff:line_{line_num}",
                        snippet=match.group()[:100],
                    ),
                    title="String concatenation in loop",
                    description="Consider using list append and join() for better performance.",
                    location=f"diff:line_{line_num}",
                ))

        # Pattern 3: List comprehension that could be generator
        list_comp_pattern = r"\[.+for\s+\w+\s+in\s+.+\]"
        for match in re.finditer(list_comp_pattern, diff_content):
            # Check if used with len(), sum(), any(), all()
            before = diff_content[max(0, match.start()-20):match.start()]
            if any(func in before for func in ["len(", "sum(", "any(", "all(", "max(", "min("]):
                line_num = diff_content[:match.start()].count('\n') + 1
                findings.append(Finding(
                    type=FindingType.PERFORMANCE,
                    severity=Severity.NIT,
                    source_agent=self.role,
                    evidence=Evidence(
                        tool="static_analysis",
                        reference=f"diff:line_{line_num}",
                        snippet=match.group()[:100],
                    ),
                    title="List comprehension could be generator",
                    description="When using with len/sum/any/all, a generator expression is more memory efficient.",
                    location=f"diff:line_{line_num}",
                ))

        return findings

    def _llm_analysis(self, context: PRContext) -> tuple[List[Finding], float, int]:
        """Perform LLM-based contextual performance analysis."""
        try:
            prompt_template = self.load_prompt()
        except FileNotFoundError:
            # Fallback if prompt not found
            prompt_template = self._get_fallback_prompt()

        analysis_context = self._build_analysis_context(context, prompt_template)

        crew_agent = Agent(
            role="Performance Analyst",
            goal="Identify performance bottlenecks, inefficient algorithms, and optimization opportunities",
            backstory=(
                "You are a performance engineering expert who can identify algorithmic inefficiencies, "
                "memory issues, and optimization opportunities in code."
            ),
            llm=self.llm,
            verbose=False,
        )

        task = Task(
            description=analysis_context,
            agent=crew_agent,
            expected_output="JSON with findings array containing performance issues and reasoning.",
        )

        result, elapsed = self._execute_with_timing(self._execute_task, crew_agent, task)

        parsed = self._parse_llm_json_output(result.get("raw_output", ""))
        findings = self._parse_findings_from_llm(parsed, FindingType.PERFORMANCE, "performance_analysis")

        return findings, elapsed, result.get("tokens", 0)

    def _build_analysis_context(self, context: PRContext, prompt_template: str) -> str:
        """Build context string for analysis."""
        pr = context.pr_metadata
        pr_context = "\n".join([
            f"PR Title: {pr.title}",
            f"Language: {pr.language}",
            f"Files Changed: {pr.files_changed}",
            f"Lines Added: {pr.lines_added}",
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
            tokens = self._extract_tokens(result)
            return {"reasoning": output[:500], "tokens": tokens, "raw_output": output}
        except Exception as e:
            logger.error(f"Error executing CrewAI task: {e}")
            return {"reasoning": f"Analysis error: {e}", "tokens": 0, "raw_output": ""}

    def _get_fallback_prompt(self) -> str:
        """Fallback prompt if file not found."""
        return """Analyze the code diff for performance issues:
        
Look for:
- Inefficient algorithms (O(n²) or worse)
- Unnecessary memory allocations
- N+1 database queries
- Blocking operations in async code
- Unnecessary object creation in loops

{pr_context}

Return JSON with findings array."""
