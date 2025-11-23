"""Domain models for code review framework.

This module defines the core data structures used throughout the system,
ensuring type safety and consistency across all components.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class FindingType(str, Enum):
    """Classification of review findings."""

    CONSISTENCY = "consistency"
    SECURITY = "security"
    STYLE = "style"
    PERFORMANCE = "performance"
    LOGIC = "logic"
    OTHER = "other"


class Severity(str, Enum):
    """Severity levels for findings."""

    NIT = "nit"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class AgentRole(str, Enum):
    """Agent roles in the system."""

    CHANGE_CONTEXT_ANALYST = "CCA"
    SECURITY_REVIEWER = "SR"
    STYLE_FORMATTER_REVIEWER = "SFR"
    REVISION_PROPOSER = "RP"
    SUPERVISOR = "Supervisor"


class SystemType(str, Enum):
    """Review system types for evaluation."""

    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"
    TOOLS_ONLY = "tools_only"


class Evidence(BaseModel):
    """Evidence supporting a finding."""

    tool: str = Field(..., description="Tool that generated the evidence")
    reference: str = Field(..., description="File path, line number, or report ID")
    snippet: Optional[str] = Field(None, description="Relevant code snippet")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class Finding(BaseModel):
    """A single review finding from an agent."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique finding ID")
    type: FindingType = Field(..., description="Classification of the finding")
    severity: Severity = Field(..., description="Severity level")
    source_agent: AgentRole = Field(..., description="Agent that created this finding")
    evidence: Evidence = Field(..., description="Supporting evidence")
    title: str = Field(..., description="Short summary of the finding")
    description: str = Field(..., description="Detailed explanation")
    has_patch: bool = Field(default=False, description="Whether a patch is available")
    patch: Optional[str] = Field(None, description="Suggested code patch")
    location: str = Field(..., description="File and line range (e.g., 'file.py:10-15')")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("patch")
    @classmethod
    def validate_patch_size(cls, v: Optional[str], info: Any) -> Optional[str]:
        """Ensure patches are reasonably sized."""
        if v is not None:
            lines = v.count("\n") + 1
            if lines > 50:  # Configurable via settings
                raise ValueError(f"Patch too large: {lines} lines (max 50)")
        return v


class PRMetadata(BaseModel):
    """Metadata about a pull request."""

    pr_id: str = Field(..., description="Unique PR identifier")
    repository: str = Field(..., description="Repository name")
    branch_source: str = Field(..., description="Source branch")
    branch_target: str = Field(..., description="Target branch")
    title: str = Field(..., description="PR title")
    description: Optional[str] = Field(None, description="PR description")
    author: str = Field(..., description="PR author")
    commit_messages: List[str] = Field(default_factory=list, description="Commit messages")
    files_changed: int = Field(default=0, description="Number of files changed")
    lines_added: int = Field(default=0, description="Lines added")
    lines_deleted: int = Field(default=0, description="Lines deleted")
    language: str = Field(..., description="Primary language (python, javascript, etc.)")


class ToolResult(BaseModel):
    """Result from running a tool."""

    tool_name: str = Field(..., description="Name of the tool")
    success: bool = Field(..., description="Whether tool ran successfully")
    output: Optional[str] = Field(None, description="Tool output")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    artifacts: Dict[str, str] = Field(
        default_factory=dict, description="Paths to generated artifacts"
    )
    execution_time_s: float = Field(..., description="Execution time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PRContext(BaseModel):
    """Complete context for a PR review."""

    correlation_id: UUID = Field(default_factory=uuid4, description="Tracking ID")
    pr_metadata: PRMetadata = Field(..., description="PR metadata")
    diff_content: str = Field(..., description="Git diff content")
    tool_results: Dict[str, ToolResult] = Field(
        default_factory=dict, description="Results from all tools"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentDecision(BaseModel):
    """Record of an agent's decision."""

    agent_role: AgentRole = Field(..., description="Agent that made the decision")
    task_description: str = Field(..., description="Task the agent was performing")
    findings: List[Finding] = Field(default_factory=list, description="Findings produced")
    reasoning: str = Field(..., description="Agent's reasoning process")
    prompt_version: str = Field(..., description="Version of prompt used")
    llm_calls: int = Field(default=0, description="Number of LLM calls made")
    tokens_used: int = Field(default=0, description="Total tokens used")
    execution_time_s: float = Field(..., description="Execution time")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PRReviewResult(BaseModel):
    """Complete review result for a PR."""

    correlation_id: UUID = Field(..., description="Links to PRContext")
    pr_id: str = Field(..., description="PR identifier")
    system_type: SystemType = Field(..., description="Type of review system used")
    change_summary: str = Field(..., description="High-level summary of changes")
    findings: List[Finding] = Field(default_factory=list, description="All findings")
    agent_decisions: List[AgentDecision] = Field(
        default_factory=list, description="Decision log from agents"
    )
    final_comment_md: str = Field(..., description="Final review comment in Markdown")
    review_time_s: float = Field(..., description="Total review time")
    token_cost_estimate: float = Field(default=0.0, description="Estimated cost in USD")
    prompt_versions: Dict[str, str] = Field(
        default_factory=dict, description="Prompt versions used"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def findings_by_severity(self) -> Dict[Severity, List[Finding]]:
        """Group findings by severity."""
        result: Dict[Severity, List[Finding]] = {s: [] for s in Severity}
        for finding in self.findings:
            result[finding.severity].append(finding)
        return result

    @property
    def findings_by_type(self) -> Dict[FindingType, List[Finding]]:
        """Group findings by type."""
        result: Dict[FindingType, List[Finding]] = {t: [] for t in FindingType}
        for finding in self.findings:
            result[finding.type].append(finding)
        return result

    @property
    def actionable_findings(self) -> List[Finding]:
        """Get findings with patches or clear action items."""
        return [f for f in self.findings if f.has_patch or f.severity in [Severity.MAJOR, Severity.CRITICAL]]


class GroundTruthLabel(BaseModel):
    """Ground truth labels for evaluation."""

    pr_id: str = Field(..., description="PR identifier")
    important_issues: List[str] = Field(
        default_factory=list,
        description="List of issue descriptions that must be caught"
    )
    false_positive_tolerance: int = Field(
        default=3,
        description="Maximum acceptable false positives"
    )
    labeler_id: str = Field(..., description="ID of person who labeled this")
    labeled_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(None, description="Additional notes")


class EvaluationResult(BaseModel):
    """Evaluation metrics for a review system."""

    system_type: SystemType = Field(..., description="System being evaluated")
    dataset_size: int = Field(..., description="Number of PRs evaluated")

    # Core metrics
    actionability_rate: float = Field(..., description="Actionable findings / total findings")
    noise_rate: float = Field(..., description="False positives / total findings")
    important_issue_coverage: float = Field(
        ...,
        description="Detected important issues / total important issues"
    )

    # Detailed metrics
    avg_findings_per_pr: float = Field(..., description="Average findings per PR")
    avg_review_time_s: float = Field(..., description="Average review time")
    avg_token_cost: float = Field(..., description="Average token cost in USD")

    # CTR/CL/SI scores (thesis-specific)
    change_type_recognition_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Accuracy in understanding change type"
    )
    change_location_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Accuracy in pinpointing issues"
    )
    solution_logic_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Quality of proposed solutions"
    )

    # Statistical data
    confidence_interval_95: Dict[str, tuple[float, float]] = Field(
        default_factory=dict,
        description="95% CI for key metrics"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
