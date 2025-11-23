"""Unit tests for metrics."""

import pytest

from domain import (
    AgentRole,
    Evidence,
    Finding,
    FindingType,
    GroundTruthLabel,
    PRReviewResult,
    Severity,
    SystemType,
)
from eval.metrics import ActionabilityMetric, CoverageMetric, NoiseMetric, PerformanceMetric
from uuid import uuid4


def create_test_result(pr_id: str, findings: list) -> PRReviewResult:
    """Helper to create test result."""
    return PRReviewResult(
        correlation_id=uuid4(),
        pr_id=pr_id,
        system_type=SystemType.MULTI_AGENT,
        change_summary="Test",
        findings=findings,
        final_comment_md="# Review",
        review_time_s=5.0,
        token_cost_estimate=0.01,
    )


def test_actionability_metric():
    """Test actionability metric calculation."""
    findings = [
        Finding(
            type=FindingType.SECURITY,
            severity=Severity.CRITICAL,
            source_agent=AgentRole.SECURITY_REVIEWER,
            evidence=Evidence(tool="semgrep", reference="file.py:1"),
            title="Critical",
            description="Issue",
            location="file.py:1",
        ),
        Finding(
            type=FindingType.STYLE,
            severity=Severity.NIT,
            source_agent=AgentRole.STYLE_FORMATTER_REVIEWER,
            evidence=Evidence(tool="ruff", reference="file.py:10"),
            title="Nit",
            description="Style",
            location="file.py:10",
            has_patch=True,
        ),
    ]
    
    result = create_test_result("001", findings)
    
    metric = ActionabilityMetric()
    values = metric.calculate([result], {})
    
    assert values["total_findings"] == 2
    assert values["actionable_findings"] == 2  # Critical + patch
    assert values["actionability_rate"] == 1.0


def test_noise_metric():
    """Test noise metric calculation."""
    findings = [
        Finding(
            type=FindingType.STYLE,
            severity=Severity.NIT,
            source_agent=AgentRole.STYLE_FORMATTER_REVIEWER,
            evidence=Evidence(tool="ruff", reference="file.py:1"),
            title="Nit without patch",
            description="Issue",
            location="file.py:1",
        ),
    ]
    
    result = create_test_result("001", findings)
    
    gt = {
        "001": GroundTruthLabel(
            pr_id="001",
            important_issues=[],
            labeler_id="test",
        )
    }
    
    metric = NoiseMetric()
    values = metric.calculate([result], gt)
    
    assert values["total_noise_findings"] == 1  # Nit without patch
    assert values["noise_rate"] == 1.0


def test_coverage_metric():
    """Test coverage metric calculation."""
    findings = [
        Finding(
            type=FindingType.SECURITY,
            severity=Severity.CRITICAL,
            source_agent=AgentRole.SECURITY_REVIEWER,
            evidence=Evidence(tool="semgrep", reference="file.py:1"),
            title="Security",
            description="SQL injection vulnerability",
            location="file.py:1",
        ),
    ]
    
    result = create_test_result("001", findings)
    
    gt = {
        "001": GroundTruthLabel(
            pr_id="001",
            important_issues=["SQL injection vulnerability"],
            labeler_id="test",
        )
    }
    
    metric = CoverageMetric()
    values = metric.calculate([result], gt)
    
    assert values["total_important_issues"] == 1
    assert values["detected_important_issues"] == 1
    assert values["important_issue_coverage"] == 1.0


def test_performance_metric():
    """Test performance metric calculation."""
    result1 = create_test_result("001", [])
    result1.review_time_s = 10.0
    result1.token_cost_estimate = 0.02
    
    result2 = create_test_result("002", [])
    result2.review_time_s = 20.0
    result2.token_cost_estimate = 0.04
    
    metric = PerformanceMetric()
    values = metric.calculate([result1, result2], {})
    
    assert values["avg_review_time_s"] == 15.0
    assert values["avg_token_cost"] == 0.03

