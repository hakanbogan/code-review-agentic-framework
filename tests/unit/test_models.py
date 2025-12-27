"""Unit tests for domain models."""

from uuid import uuid4

from domain import (
    AgentRole,
    Evidence,
    Finding,
    FindingType,
    PRMetadata,
    PRReviewResult,
    Severity,
    SystemType,
    Language
)


def test_evidence_creation():
    """Test Evidence model creation."""
    evidence = Evidence(
        tool="ruff",
        reference="file.py:10",
        snippet="def foo():",
        metadata={"severity": "high"},
    )

    assert evidence.tool == "ruff"
    assert evidence.reference == "file.py:10"
    assert evidence.metadata["severity"] == "high"


def test_finding_creation():
    """Test Finding model creation."""
    evidence = Evidence(tool="semgrep", reference="auth.py:42")

    finding = Finding(
        type=FindingType.SECURITY,
        severity=Severity.CRITICAL,
        source_agent=AgentRole.SECURITY_REVIEWER,
        evidence=evidence,
        title="SQL Injection vulnerability",
        description="Unsafe SQL query construction",
        location="auth.py:42-45",
    )

    assert finding.type == FindingType.SECURITY
    assert finding.severity == Severity.CRITICAL
    assert finding.source_agent == AgentRole.SECURITY_REVIEWER
    assert finding.has_patch is False


def test_finding_patch_validation():
    """Test patch size validation."""
    evidence = Evidence(tool="ruff", reference="file.py:1")

    # Should pass - small patch
    finding = Finding(
        type=FindingType.STYLE,
        severity=Severity.NIT,
        source_agent=AgentRole.STYLE_FORMATTER_REVIEWER,
        evidence=evidence,
        title="Style fix",
        description="Fix indentation",
        location="file.py:1",
        has_patch=True,
        patch="def foo():\n    pass",
    )

    assert finding.patch is not None


def test_pr_metadata_creation():
    """Test PRMetadata creation."""
    metadata = PRMetadata(
        pr_id="123",
        repository="test-repo",
        branch_source="feature",
        branch_target="main",
        title="Add feature",
        author="developer",
        language=Language.PYTHON,
    )

    assert metadata.pr_id == "123"
    assert metadata.language == Language.PYTHON


def test_pr_review_result_findings_grouping():
    """Test findings grouping in PRReviewResult."""
    correlation_id = uuid4()

    findings = [
        Finding(
            type=FindingType.SECURITY,
            severity=Severity.CRITICAL,
            source_agent=AgentRole.SECURITY_REVIEWER,
            evidence=Evidence(tool="semgrep", reference="file.py:1"),
            title="Security issue",
            description="Vuln",
            location="file.py:1",
        ),
        Finding(
            type=FindingType.STYLE,
            severity=Severity.NIT,
            source_agent=AgentRole.STYLE_FORMATTER_REVIEWER,
            evidence=Evidence(tool="ruff", reference="file.py:10"),
            title="Style issue",
            description="Format",
            location="file.py:10",
        ),
    ]

    result = PRReviewResult(
        correlation_id=correlation_id,
        pr_id="123",
        system_type=SystemType.MULTI_AGENT,
        change_summary="Test review",
        findings=findings,
        final_comment_md="# Review",
        review_time_s=5.0,
    )

    by_severity = result.findings_by_severity
    assert len(by_severity[Severity.CRITICAL]) == 1
    assert len(by_severity[Severity.NIT]) == 1

    by_type = result.findings_by_type
    assert len(by_type[FindingType.SECURITY]) == 1
    assert len(by_type[FindingType.STYLE]) == 1


def test_actionable_findings():
    """Test actionable findings property."""
    correlation_id = uuid4()

    findings = [
        Finding(
            type=FindingType.SECURITY,
            severity=Severity.CRITICAL,
            source_agent=AgentRole.SECURITY_REVIEWER,
            evidence=Evidence(tool="semgrep", reference="file.py:1"),
            title="Critical",
            description="Critical issue",
            location="file.py:1",
        ),
        Finding(
            type=FindingType.STYLE,
            severity=Severity.NIT,
            source_agent=AgentRole.STYLE_FORMATTER_REVIEWER,
            evidence=Evidence(tool="ruff", reference="file.py:10"),
            title="Nit",
            description="Nit issue",
            location="file.py:10",
            has_patch=True,
        ),
    ]

    result = PRReviewResult(
        correlation_id=correlation_id,
        pr_id="123",
        system_type=SystemType.MULTI_AGENT,
        change_summary="Test",
        findings=findings,
        final_comment_md="# Review",
        review_time_s=5.0,
    )

    actionable = result.actionable_findings
    assert len(actionable) == 2  # Critical + nit with patch
