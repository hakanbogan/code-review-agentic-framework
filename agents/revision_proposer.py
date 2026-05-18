"""Revision Proposer agent."""

from typing import List

from crewai import Agent, Crew, Task

from agents.base import BaseAgent
from app.config import Settings
from app.logging import get_logger
from domain import AgentDecision, AgentRole, Finding, PRContext, Severity

logger = get_logger(__name__)


class RevisionProposer(BaseAgent):
    """Proposes code revisions based on other agents' findings."""

    def __init__(self, settings: Settings, upstream_decisions: List[AgentDecision]):
        super().__init__(AgentRole.REVISION_PROPOSER, settings)
        self.upstream_decisions = upstream_decisions
        self.max_patch_lines = settings.max_patch_lines

    def analyze(self, context: PRContext) -> AgentDecision:
        """Propose revisions based on upstream findings."""
        logger.info("Revision Proposer starting analysis", extra={"pr_id": context.pr_metadata.pr_id})

        # Collect findings that need patches
        upstream_findings = [f for d in self.upstream_decisions for f in d.findings]
        findings_needing_patches = [
            f for f in upstream_findings
            if not f.has_patch and f.severity in [Severity.MAJOR, Severity.CRITICAL]
        ]

        # Generate patches for high-priority findings (limited to 5)
        patched, elapsed, tokens = self._generate_patches(context, findings_needing_patches[:5])
        validated = self._validate_findings(patched)

        logger.info(f"Revision Proposer completed: {len(validated)} patches")

        return self._create_decision(
            task_description="Generate code revision proposals",
            findings=validated,
            reasoning=f"Generated patches for {len(validated)} high-priority findings",
            llm_calls=len(findings_needing_patches[:5]),
            tokens_used=tokens,
            execution_time=elapsed,
        )

    def _generate_patches(
        self,
        context: PRContext,
        findings: List[Finding]
    ) -> tuple[List[Finding], float, int]:
        """Generate patches for findings using LLM."""
        if not findings:
            return [], 0.0, 0

        total_time = 0.0
        total_tokens = 0
        patched_findings = []

        for finding in findings:
            try:
                patch, elapsed, tokens = self._generate_single_patch(context, finding)
                total_time += elapsed
                total_tokens += tokens

                if patch:
                    finding.has_patch = True
                    finding.patch = patch
                    patched_findings.append(finding)
            except Exception as e:
                logger.warning(f"Failed to generate patch for {finding.id}: {e}")

        return patched_findings, total_time, total_tokens

    def _generate_single_patch(
        self,
        context: PRContext,
        finding: Finding
    ) -> tuple[str | None, float, int]:
        """Generate a single patch for a finding."""
        crew_agent = Agent(
            role="Code Fixer",
            goal="Generate minimal, correct code patches to fix identified issues",
            backstory=(
                "You are an expert programmer who writes clean, minimal patches "
                "that fix issues without introducing new problems."
            ),
            llm=self.llm,
            verbose=False,
        )

        # Extract relevant code context
        diff_section = self._extract_relevant_diff(context.diff_content, finding.location)

        task_description = f"""Generate a code patch to fix this issue:

Issue: {finding.title}
Description: {finding.description}
Location: {finding.location}
Severity: {finding.severity.value}

Relevant code:
{diff_section}

Requirements:
1. Generate ONLY the patch (no explanation)
2. Use unified diff format
3. Keep patch minimal (max {self.max_patch_lines} lines)
4. Ensure the fix is correct and complete

Return the patch as a code block."""

        task = Task(
            description=task_description,
            agent=crew_agent,
            expected_output="A unified diff patch that fixes the issue.",
        )

        result, elapsed = self._execute_with_timing(self._execute_task, crew_agent, task)

        # Extract patch from result
        patch = self._extract_patch(result.get("raw_output", ""))

        return patch, elapsed, result.get("tokens", 0)

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
            return {"reasoning": f"Error: {e}", "tokens": 0, "raw_output": ""}

    def _extract_relevant_diff(self, diff_content: str, location: str) -> str:
        """Extract diff section relevant to the finding location."""
        if not location or ":" not in location:
            return diff_content[:2000]

        # Try to find file in diff
        file_path = location.split(":")[0]
        lines = diff_content.split("\n")

        relevant_lines = []
        in_file = False
        line_count = 0

        for line in lines:
            if line.startswith("+++") and file_path in line:
                in_file = True
            elif line.startswith("+++") and in_file:
                break  # Next file

            if in_file:
                relevant_lines.append(line)
                line_count += 1
                if line_count > 100:
                    break

        return "\n".join(relevant_lines) if relevant_lines else diff_content[:2000]

    def _extract_patch(self, raw_output: str) -> str | None:
        """Extract patch from LLM output."""
        import re

        # Try to find code block
        patterns = [
            r"```diff\s*([\s\S]*?)\s*```",
            r"```patch\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, raw_output)
            if matches:
                patch = matches[0].strip()
                # Validate it looks like a patch
                if any(line.startswith(("+", "-", "@@")) for line in patch.split("\n")):
                    # Limit size
                    lines = patch.split("\n")
                    if len(lines) > self.max_patch_lines:
                        lines = lines[:self.max_patch_lines]
                        lines.append("# ... patch truncated")
                    return "\n".join(lines)

        return None
