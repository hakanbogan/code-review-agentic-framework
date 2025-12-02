"""Test Coverage Reviewer agent."""

import re
from typing import List

from crewai import Agent, Crew, Task

from agents.base import BaseAgent
from app.config import Settings
from app.logging import get_logger
from domain import AgentDecision, AgentRole, Evidence, Finding, FindingType, PRContext, Severity

logger = get_logger(__name__)


class TestCoverageReviewer(BaseAgent):
    """Reviews test coverage and quality using hybrid approach (tool + LLM)."""

    def __init__(self, settings: Settings):
        super().__init__(AgentRole.TEST_REVIEWER, settings)

    def analyze(self, context: PRContext) -> AgentDecision:
        """Analyze test coverage and quality."""
        logger.info("Test Coverage Reviewer starting analysis", extra={"pr_id": context.pr_metadata.pr_id})

        findings = []

        # Phase 1: Static analysis for test patterns
        static_findings = self._static_analysis(context)
        findings.extend(static_findings)

        # Phase 2: Coverage tool results if available
        if "coverage_reader" in context.tool_results:
            coverage_findings = self._analyze_coverage(context)
            findings.extend(coverage_findings)

        # Phase 3: LLM-based test quality analysis
        llm_findings, elapsed, tokens = self._llm_analysis(context)
        findings.extend(llm_findings)

        validated = self._validate_findings(findings)

        logger.info(f"Test Coverage Reviewer completed: {len(validated)} findings")

        return self._create_decision(
            task_description="Review test coverage and quality",
            findings=validated,
            reasoning=f"Static: {len(static_findings)}, LLM: {len(llm_findings)}",
            llm_calls=1,
            tokens_used=tokens,
            execution_time=elapsed,
        )

    def _static_analysis(self, context: PRContext) -> List[Finding]:
        """Analyze diff for test-related patterns."""
        findings = []
        diff = context.diff_content

        # Check if new code is added without tests
        added_files = re.findall(r"\+\+\+ b/(.+\.py)", diff)
        test_files = [f for f in added_files if "test" in f.lower()]
        source_files = [f for f in added_files if "test" not in f.lower()]

        # If source files added but no test files
        if source_files and not test_files:
            # Check if there are function/class definitions
            new_functions = re.findall(r"\+\s*def\s+(\w+)\s*\(", diff)
            new_classes = re.findall(r"\+\s*class\s+(\w+)", diff)

            if new_functions or new_classes:
                items = new_functions + new_classes
                findings.append(Finding(
                    type=FindingType.OTHER,
                    severity=Severity.MINOR,
                    source_agent=self.role,
                    evidence=Evidence(
                        tool="static_analysis",
                        reference=", ".join(source_files[:3]),
                        snippet=f"New items: {', '.join(items[:5])}",
                    ),
                    title="New code without corresponding tests",
                    description=(
                        f"New functions/classes added ({len(items)} items) but no test files modified. "
                        "Consider adding unit tests for new functionality."
                    ),
                    location=source_files[0] if source_files else "unknown",
                ))

        # Check for test assertions
        test_content = "\n".join(
            line for line in diff.split("\n")
            if line.startswith("+") and "test" in line.lower()
        )

        if test_files and "assert" not in test_content and "self.assert" not in test_content:
            findings.append(Finding(
                type=FindingType.OTHER,
                severity=Severity.MINOR,
                source_agent=self.role,
                evidence=Evidence(
                    tool="static_analysis",
                    reference=test_files[0],
                    snippet="No assertions found in test changes",
                ),
                title="Test file modified without assertions",
                description="Test file changes don't include assertions. Tests should verify expected behavior.",
                location=test_files[0],
            ))

        return findings

    def _analyze_coverage(self, context: PRContext) -> List[Finding]:
        """Analyze coverage tool results."""
        findings = []
        coverage_result = context.tool_results.get("coverage_reader")

        if not coverage_result or not coverage_result.success:
            return findings

        import json
        try:
            data = json.loads(coverage_result.output)
            total_coverage = data.get("summary", {}).get("percent_covered", 0)

            if total_coverage < 80:
                findings.append(Finding(
                    type=FindingType.OTHER,
                    severity=Severity.MINOR if total_coverage > 60 else Severity.MAJOR,
                    source_agent=self.role,
                    evidence=Evidence(
                        tool="coverage",
                        reference="coverage_report",
                        snippet=f"Total coverage: {total_coverage:.1f}%",
                    ),
                    title=f"Low test coverage: {total_coverage:.1f}%",
                    description=f"Project coverage is {total_coverage:.1f}%, below the 80% threshold.",
                    location="project",
                ))

            # Find files with low coverage
            for file_data in data.get("files", []):
                file_coverage = file_data.get("percent_covered", 0)
                if file_coverage < 50:
                    findings.append(Finding(
                        type=FindingType.OTHER,
                        severity=Severity.NIT,
                        source_agent=self.role,
                        evidence=Evidence(
                            tool="coverage",
                            reference=file_data.get("path", "unknown"),
                            snippet=f"Coverage: {file_coverage:.1f}%",
                        ),
                        title=f"Low coverage in {file_data.get('path', 'file')}",
                        description=f"File has only {file_coverage:.1f}% coverage.",
                        location=file_data.get("path", "unknown"),
                    ))

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse coverage data: {e}")

        return findings

    def _llm_analysis(self, context: PRContext) -> tuple[List[Finding], float, int]:
        """LLM-based test quality analysis."""
        try:
            prompt_template = self.load_prompt()
        except FileNotFoundError:
            prompt_template = self._get_fallback_prompt()

        analysis_context = self._build_analysis_context(context, prompt_template)

        crew_agent = Agent(
            role="Test Quality Analyst",
            goal="Evaluate test quality, identify missing test cases, and suggest improvements",
            backstory=(
                "You are a QA expert who ensures comprehensive test coverage, "
                "identifies edge cases that need testing, and maintains test quality standards."
            ),
            llm=self.llm,
            verbose=False,
        )

        task = Task(
            description=analysis_context,
            agent=crew_agent,
            expected_output="JSON with findings array about test quality and missing tests.",
        )

        result, elapsed = self._execute_with_timing(self._execute_task, crew_agent, task)

        parsed = self._parse_llm_json_output(result.get("raw_output", ""))
        findings = self._parse_findings_from_llm(parsed, FindingType.OTHER, "test_analysis")

        return findings, elapsed, result.get("tokens", 0)

    def _build_analysis_context(self, context: PRContext, prompt_template: str) -> str:
        """Build context string for analysis."""
        pr = context.pr_metadata
        pr_context = "\n".join([
            f"PR Title: {pr.title}",
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
        return """Review test coverage and quality in the code changes:

Analyze:
- Are new functions/classes tested?
- Are edge cases covered?
- Is test quality good (proper assertions, isolation)?
- Are integration tests needed?
- Are mocks used appropriately?

{pr_context}

Return JSON with findings array."""
