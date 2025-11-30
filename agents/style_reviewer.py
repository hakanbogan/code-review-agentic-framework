"""Style and Format Reviewer agent."""

import json
from typing import List

from crewai import Agent
from langchain_openai import ChatOpenAI

from agents.base import BaseAgent
from app.config import Settings
from domain import (
    AgentDecision,
    AgentRole,
    Evidence,
    Finding,
    FindingType,
    PRContext,
    Severity,
)
from app.logging import get_logger

logger = get_logger(__name__)


class StyleFormatReviewer(BaseAgent):
    """Reviews code style and formatting issues."""

    def __init__(self, settings: Settings):
        super().__init__(AgentRole.STYLE_FORMATTER_REVIEWER, settings)
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            model_kwargs={"seed": settings.openai_seed},
        )
        self.max_nits = settings.max_nits_per_review

    def analyze(self, context: PRContext) -> AgentDecision:
        """Analyze style and format issues.

        Args:
            context: Complete PR context

        Returns:
            AgentDecision with style findings
        """
        logger.info(
            "Style & Format Reviewer starting analysis",
            extra={"pr_id": context.pr_metadata.pr_id}
        )

        findings = []

        # Analyze ruff results (Python)
        if "ruff" in context.tool_results:
            findings.extend(self._analyze_ruff(context))

        # Analyze eslint results (JS/TS)
        if "eslint" in context.tool_results:
            findings.extend(self._analyze_eslint(context))

        # Apply nit limit
        findings = self._apply_nit_limit(findings)

        validated_findings = self._validate_findings(findings)

        logger.info(
            f"Style & Format Reviewer completed: {len(validated_findings)} findings",
            extra={"pr_id": context.pr_metadata.pr_id}
        )

        return self._create_decision(
            task_description="Review code style and formatting",
            findings=validated_findings,
            reasoning="Analyzed linter output and applied nit limits",
            llm_calls=0,
            tokens_used=0,
            execution_time=0.0,
        )

    def _analyze_ruff(self, context: PRContext) -> List[Finding]:
        """Analyze ruff linter results."""
        findings = []
        ruff_result = context.tool_results["ruff"]

        if not ruff_result.success or not ruff_result.output:
            return findings

        try:
            # Parse ruff output directly - it's a JSON list
            violations_list = []

            if ruff_result.output:
                try:
                    violations_data = json.loads(ruff_result.output)
                    if isinstance(violations_data, list):
                        violations_list = violations_data
                    elif isinstance(violations_data, dict):
                        violations_list = violations_data.get("violations", [])
                except (json.JSONDecodeError, AttributeError) as e:
                    logger.warning(f"Failed to parse ruff output: {e}")
                    return findings

            for violation in violations_list:
                # Ensure violation is a dict
                if not isinstance(violation, dict):
                    logger.warning(f"Skipping non-dict violation: {type(violation)}")
                    continue

                # Get location safely
                location_obj = violation.get("location")
                if isinstance(location_obj, dict):
                    row = location_obj.get("row", 0)
                    column = location_obj.get("column", 0)
                else:
                    # Try direct row/column in violation
                    row = violation.get("row", 0)
                    column = violation.get("column", 0)
                    location_obj = {"row": row, "column": column}

                # Handle patch - ruff fix is a dict with 'message' and 'edits'
                fix_obj = violation.get("fix")
                patch_str = None
                if fix_obj:
                    if isinstance(fix_obj, dict):
                        # Extract patch from ruff fix format
                        edits = fix_obj.get("edits", [])
                        if edits:
                            # Convert edits to patch string
                            patch_parts = []
                            for edit in edits:
                                if isinstance(edit, dict):
                                    content_obj = edit.get("content", {})
                                    if isinstance(content_obj, dict):
                                        content = content_obj.get("text", "")
                                    else:
                                        content = str(content_obj)
                                else:
                                    content = str(edit)
                                if content:
                                    patch_parts.append(content)
                            patch_str = "\n".join(patch_parts) if patch_parts else None
                    elif isinstance(fix_obj, str):
                        patch_str = fix_obj

                filename = violation.get("filename", "unknown")
                # Extract just filename if full path
                if "/" in str(filename):
                    filename = str(filename).split("/")[-1]

                finding = Finding(
                    type=FindingType.STYLE,
                    severity=Severity.NIT,
                    source_agent=self.role,
                    evidence=Evidence(
                        tool="ruff",
                        reference=f"{filename}:{row}",
                        snippet="",
                        metadata={
                            "code": violation.get("code"),
                            "url": violation.get("url"),
                        },
                    ),
                    title=f"[{violation.get('code', '')}] Style violation",
                    description=violation.get("message", ""),
                    location=f"{filename}:{row}",
                    has_patch=patch_str is not None,
                    patch=patch_str,
                )
                findings.append(finding)
        except json.JSONDecodeError:
            logger.error("Failed to parse ruff output")

        return findings

    def _analyze_eslint(self, context: PRContext) -> List[Finding]:
        """Analyze eslint results."""
        findings = []
        eslint_result = context.tool_results["eslint"]

        if not eslint_result.success or not eslint_result.output:
            return findings

        try:
            data = json.loads(eslint_result.output)
            for file_result in data.get("files", []):
                filename = file_result.get("filename", "")
                for message in file_result.get("messages", []):
                    severity = Severity.MINOR if message.get("severity") == 2 else Severity.NIT

                    finding = Finding(
                        type=FindingType.STYLE,
                        severity=severity,
                        source_agent=self.role,
                        evidence=Evidence(
                            tool="eslint",
                            reference=f"{filename}:{message.get('line', 0)}",
                            snippet="",
                            metadata={
                                "rule_id": message.get("rule_id"),
                            },
                        ),
                        title=f"[{message.get('rule_id', '')}] Style violation",
                        description=message.get("message", ""),
                        location=f"{filename}:{message.get('line', 0)}",
                    )
                    findings.append(finding)
        except json.JSONDecodeError:
            logger.error("Failed to parse eslint output")

        return findings

    def _apply_nit_limit(self, findings: List[Finding]) -> List[Finding]:
        """Apply maximum nit limit, keeping most important issues."""
        nits = [f for f in findings if f.severity == Severity.NIT]
        others = [f for f in findings if f.severity != Severity.NIT]

        if len(nits) <= self.max_nits:
            return findings

        # Keep nits with fixes first
        nits_with_fix = [f for f in nits if f.has_patch]
        nits_without_fix = [f for f in nits if not f.has_patch]

        limited_nits = (nits_with_fix + nits_without_fix)[:self.max_nits]

        logger.info(
            f"Applied nit limit: {len(nits)} -> {len(limited_nits)}",
            extra={"max_nits": self.max_nits}
        )

        return others + limited_nits
