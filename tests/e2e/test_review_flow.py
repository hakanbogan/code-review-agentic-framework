"""End-to-end tests for review flow."""

from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.config import Settings
from domain import Language, PRMetadata
from flows import ReviewFlow


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    return Settings(
        openai_api_key="test-key",
        openai_model="gpt-4-turbo-preview",
        openai_temperature=0.0,
        openai_seed=42,
    )


@pytest.fixture
def test_pr_metadata():
    """Create test PR metadata."""
    return PRMetadata(
        pr_id="test-001",
        repository="test-repo",
        branch_source="feature",
        branch_target="main",
        title="Test PR",
        description="Test description",
        author="developer",
        language=Language.PYTHON,
    )


@patch("flows.context_builder.ContextBuilder.build_context")
@patch("agents.change_context_analyst.ChangeContextAnalyst.analyze")
def test_single_agent_review(mock_analyze, mock_build_context, mock_settings, test_pr_metadata):
    """Test single-agent review flow."""
    from domain import AgentDecision, AgentRole, PRContext, ToolResult

    # Mock context
    mock_context = PRContext(
        correlation_id=uuid4(),
        pr_metadata=test_pr_metadata,
        diff_content="mock diff",
        tool_results={
            "git_diff": ToolResult(
                tool_name="git_diff",
                success=True,
                output="mock diff",
                execution_time_s=0.1,
            )
        },
    )
    mock_build_context.return_value = mock_context

    # Mock agent decision
    mock_decision = AgentDecision(
        agent_role=AgentRole.CHANGE_CONTEXT_ANALYST,
        task_description="Test",
        findings=[],
        reasoning="Test reasoning",
        prompt_version="v1",
        llm_calls=1,
        tokens_used=100,
        execution_time_s=1.0,
    )
    mock_analyze.return_value = mock_decision

    # Run review
    flow = ReviewFlow(mock_settings, language=Language.PYTHON)
    result = flow.run_single_agent_review(
        test_pr_metadata,
        Path("/tmp/test-repo"),
    )

    assert result.pr_id == "test-001"
    assert result.system_type.value == "single_agent"
    assert len(result.agent_decisions) >= 1


@patch("flows.context_builder.ContextBuilder.build_context")
@patch("agents.change_context_analyst.ChangeContextAnalyst.analyze")
@patch("agents.security_reviewer.SecurityReviewer.analyze")
@patch("agents.style_reviewer.StyleFormatReviewer.analyze")
@patch("agents.revision_proposer.RevisionProposer.analyze")
@patch("agents.supervisor.Supervisor.analyze")
def test_multi_agent_review(
    mock_supervisor,
    mock_proposer,
    mock_style,
    mock_security,
    mock_cca,
    mock_build_context,
    mock_settings,
    test_pr_metadata,
):
    """Test multi-agent review flow."""
    from domain import AgentDecision, AgentRole, PRContext, ToolResult

    # Mock context
    mock_context = PRContext(
        correlation_id=uuid4(),
        pr_metadata=test_pr_metadata,
        diff_content="mock diff",
        tool_results={},
    )
    mock_build_context.return_value = mock_context

    # Mock all agent decisions
    def create_mock_decision(role):
        return AgentDecision(
            agent_role=role,
            task_description="Test",
            findings=[],
            reasoning="Test",
            prompt_version="v1",
            llm_calls=1,
            tokens_used=100,
            execution_time_s=1.0,
        )

    mock_cca.return_value = create_mock_decision(AgentRole.CHANGE_CONTEXT_ANALYST)
    mock_security.return_value = create_mock_decision(AgentRole.SECURITY_REVIEWER)
    mock_style.return_value = create_mock_decision(AgentRole.STYLE_FORMATTER_REVIEWER)
    mock_proposer.return_value = create_mock_decision(AgentRole.REVISION_PROPOSER)
    mock_supervisor.return_value = create_mock_decision(AgentRole.SUPERVISOR)

    # Run review
    flow = ReviewFlow(mock_settings, language=Language.PYTHON)
    result = flow.run_multi_agent_review(
        test_pr_metadata,
        Path("/tmp/test-repo"),
    )

    assert result.pr_id == "test-001"
    assert result.system_type.value == "multi_agent"
    assert len(result.agent_decisions) >= 5  # All agents ran
