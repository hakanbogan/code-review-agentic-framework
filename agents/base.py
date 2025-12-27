"""Base class for all review agents."""

import json
import re
from abc import ABC, abstractmethod
from time import time
from typing import Any, Dict, List

from langchain_core.callbacks import BaseCallbackHandler
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from app.config import Settings
from app.logging import get_logger
from domain import AgentDecision, AgentRole, Evidence, Finding, FindingType, LLMProvider, PRContext, Severity

logger = get_logger(__name__)


class TokenUsageCallback(BaseCallbackHandler):
    """Callback to track token usage from LLM calls."""

    def __init__(self):
        super().__init__()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def on_llm_end(self, response, **kwargs):
        """Capture token usage from LLM response."""
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            self.total_input_tokens += usage.get("prompt_tokens", 0)
            self.total_output_tokens += usage.get("completion_tokens", 0)
        # Also check response.usage_metadata for newer LangChain versions
        elif hasattr(response, "usage_metadata"):
            if hasattr(response.usage_metadata, "input_tokens"):
                self.total_input_tokens += response.usage_metadata.input_tokens
            if hasattr(response.usage_metadata, "output_tokens"):
                self.total_output_tokens += response.usage_metadata.output_tokens

    @property
    def total_tokens(self) -> int:
        """Get total tokens used."""
        return self.total_input_tokens + self.total_output_tokens


class BaseAgent(ABC):
    """Abstract base class for all review agents."""

    def __init__(self, role: AgentRole, settings: Settings):
        self.role = role
        self.settings = settings
        self.prompt_version = settings.default_prompt_version
        self.token_callback = TokenUsageCallback()
        self.llm = self._create_llm(settings)

    def _create_llm(self, settings: Settings) -> ChatOpenAI | ChatAnthropic:
        """Create LLM instance with consistent configuration based on provider."""
        if settings.llm_provider == LLMProvider.ANTHROPIC:
            return ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model=settings.anthropic_model,
                temperature=settings.openai_temperature,
                callbacks=[self.token_callback],
            )
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            seed=settings.openai_seed,
            callbacks=[self.token_callback],
        )

    @abstractmethod
    def analyze(self, context: PRContext) -> AgentDecision:
        """Analyze PR context and produce findings."""
        pass

    def load_prompt(self) -> str:
        """Load prompt template for this agent."""
        prompt_path = self.settings.get_prompt_path(self.role.value, self.prompt_version)
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
        return result, time() - start

    def _reset_token_tracking(self) -> None:
        """Reset token callback counters."""
        self.token_callback.total_input_tokens = 0
        self.token_callback.total_output_tokens = 0

    def _get_token_count(self) -> int:
        """Get total tokens used from callback."""
        return self.token_callback.total_tokens

    def _validate_findings(self, findings: List[Finding]) -> List[Finding]:
        """Validate findings meet evidence requirements."""
        valid = []
        for f in findings:
            if not f.evidence.tool or not f.evidence.reference:
                logger.warning(f"Rejecting finding without evidence: {f.id}")
                continue
            valid.append(f)
        return valid

    @staticmethod
    def severity_rank(severity: Severity) -> int:
        """Get numeric rank for severity."""
        return {Severity.CRITICAL: 4, Severity.MAJOR: 3, Severity.MINOR: 2, Severity.NIT: 1}.get(severity, 0)

    @staticmethod
    def type_priority(finding_type: FindingType) -> int:
        """Get priority score for finding type."""
        return {
            FindingType.SECURITY: 5,
            FindingType.LOGIC: 4,
            FindingType.PERFORMANCE: 3,
            FindingType.CONSISTENCY: 2,
            FindingType.STYLE: 1,
            FindingType.OTHER: 0,
        }.get(finding_type, 0)

    def _apply_nit_limit(self, findings: List[Finding], max_nits: int) -> List[Finding]:
        """Apply maximum nit limit, keeping most important issues."""
        nits = [f for f in findings if f.severity == Severity.NIT]
        others = [f for f in findings if f.severity != Severity.NIT]

        if len(nits) <= max_nits:
            return findings

        # Prioritize nits with patches
        nits_sorted = sorted(nits, key=lambda f: (f.has_patch, self.type_priority(f.type)), reverse=True)
        limited = nits_sorted[:max_nits]

        logger.info(f"Applied nit limit: {len(nits)} -> {len(limited)}")
        return others + limited

    def _parse_llm_json_output(self, raw_output: str) -> Dict[str, Any]:
        """Parse LLM output as JSON, handling markdown code blocks.

        Args:
            raw_output: Raw LLM output string

        Returns:
            Parsed JSON dict with findings and reasoning
        """
        if not raw_output:
            return {"findings": [], "reasoning": "No output from LLM"}

        # Try to extract JSON from markdown code blocks
        json_patterns = [
            r"```json\s*([\s\S]*?)\s*```",  # ```json ... ```
            r"```\s*([\s\S]*?)\s*```",       # ``` ... ```
            r"\{[\s\S]*\}",                   # Raw JSON object
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, raw_output)
            for match in matches:
                try:
                    parsed = json.loads(match.strip())
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    continue

        # If no valid JSON found, return with raw output as reasoning
        return {"findings": [], "reasoning": raw_output[:500]}

    def _parse_findings_from_llm(
        self,
        llm_output: Dict[str, Any],
        finding_type: FindingType,
        tool_name: str,
    ) -> List[Finding]:
        """Convert parsed LLM output to Finding objects.

        Args:
            llm_output: Parsed LLM output dict
            finding_type: Default finding type for this agent
            tool_name: Tool name for evidence

        Returns:
            List of Finding objects
        """
        findings = []
        raw_findings = llm_output.get("findings", [])

        if not isinstance(raw_findings, list):
            return findings

        for data in raw_findings:
            if not isinstance(data, dict):
                continue

            try:
                # Map severity string to enum
                severity_str = data.get("severity", "minor").lower()
                severity = {
                    "critical": Severity.CRITICAL,
                    "major": Severity.MAJOR,
                    "minor": Severity.MINOR,
                    "nit": Severity.NIT,
                }.get(severity_str, Severity.MINOR)

                # Map type string to enum if provided
                type_str = data.get("type", finding_type.value).lower()
                f_type = {
                    "security": FindingType.SECURITY,
                    "logic": FindingType.LOGIC,
                    "performance": FindingType.PERFORMANCE,
                    "consistency": FindingType.CONSISTENCY,
                    "style": FindingType.STYLE,
                }.get(type_str, finding_type)

                # Extract evidence
                evidence_data = data.get("evidence", {})
                if isinstance(evidence_data, dict):
                    evidence = Evidence(
                        tool=tool_name,
                        reference=evidence_data.get("reference", data.get("location", "")),
                        snippet=evidence_data.get("snippet", ""),
                        metadata=evidence_data.get("metadata", {}),
                    )
                else:
                    evidence = Evidence(
                        tool=tool_name,
                        reference=data.get("location", ""),
                        snippet="",
                    )

                finding = Finding(
                    type=f_type,
                    severity=severity,
                    source_agent=self.role,
                    evidence=evidence,
                    title=data.get("title", "Issue found"),
                    description=data.get("description", ""),
                    location=data.get("location", ""),
                    has_patch=bool(data.get("patch")),
                    patch=data.get("patch"),
                )
                findings.append(finding)

            except Exception as e:
                logger.warning(f"Failed to parse finding: {e}")
                continue

        return findings
