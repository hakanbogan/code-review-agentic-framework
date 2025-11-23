"""Base class for all review agents."""

from abc import ABC, abstractmethod
from pathlib import Path
from time import time
from typing import List

from domain import AgentDecision, AgentRole, Finding, PRContext
from app.config import Settings
from app.logging import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all review agents."""

    def __init__(self, role: AgentRole, settings: Settings):
        self.role = role
        self.settings = settings
        self.prompt_version = settings.default_prompt_version

    @abstractmethod
    def analyze(self, context: PRContext) -> AgentDecision:
        """Analyze PR context and produce findings.

        Args:
            context: Complete PR context

        Returns:
            AgentDecision with findings and reasoning
        """
        pass

    def load_prompt(self) -> str:
        """Load prompt template for this agent."""
        prompt_path = self.settings.get_prompt_path(
            self.role.value,
            self.prompt_version
        )

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")

        return prompt_path.read_text()

    def _create_decision(
        self,
        task_description: str,
        findings: List[Finding],
        reasoning: str,
        llm_calls: int = 0,
        tokens_used: int = 0,
        execution_time: float = 0.0,
    ) -> AgentDecision:
        """Create agent decision record."""
        return AgentDecision(
            agent_role=self.role,
            task_description=task_description,
            findings=findings,
            reasoning=reasoning,
            prompt_version=self.prompt_version,
            llm_calls=llm_calls,
            tokens_used=tokens_used,
            execution_time_s=execution_time,
        )

    def _execute_with_timing(self, func, *args, **kwargs):
        """Execute function with timing."""
        start = time()
        result = func(*args, **kwargs)
        elapsed = time() - start
        return result, elapsed

    def _validate_findings(self, findings: List[Finding]) -> List[Finding]:
        """Validate findings meet evidence requirements.

        Args:
            findings: List of findings to validate

        Returns:
            Filtered list of valid findings with evidence
        """
        valid_findings = []

        for finding in findings:
            if not finding.evidence.tool:
                logger.warning(
                    f"Rejecting finding without tool evidence: {finding.id}",
                    extra={"agent": self.role.value}
                )
                continue

            if not finding.evidence.reference:
                logger.warning(
                    f"Rejecting finding without reference: {finding.id}",
                    extra={"agent": self.role.value}
                )
                continue

            valid_findings.append(finding)

        return valid_findings
