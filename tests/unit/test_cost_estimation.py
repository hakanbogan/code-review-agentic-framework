"""Unit tests for ReviewFlow._estimate_cost pricing-table coverage."""

from unittest.mock import MagicMock, patch

from app.config import Settings
from domain import LLMProvider
from flows import ReviewFlow


def _build_flow(model_id: str) -> ReviewFlow:
    """Construct a ReviewFlow with the given Anthropic model.

    The tool registry is mocked so the test does not shell out to ruff,
    bandit, semgrep, or git at construction time.
    """
    settings = Settings(
        llm_provider=LLMProvider.ANTHROPIC,
        anthropic_api_key="test-key",
        anthropic_model=model_id,
    )
    with patch("flows.review_flow.create_tool_registry", return_value=MagicMock()):
        return ReviewFlow(settings)


def test_estimate_cost_recognizes_claude_4x():
    """Claude 4.x models hit their dedicated pricing branches, not the fallback."""
    # 1M tokens split 70/30 (input/output) per the function's fallback assumption.

    # Haiku 4.x: $1 in, $5 out  ->  0.7*1 + 0.3*5 = 2.20
    assert _build_flow("claude-haiku-4-5-20251001")._estimate_cost(1_000_000) == 2.20
    assert _build_flow("claude-haiku-4")._estimate_cost(1_000_000) == 2.20

    # Sonnet 4.x: $3 in, $15 out  ->  0.7*3 + 0.3*15 = 6.60
    assert _build_flow("claude-sonnet-4-6")._estimate_cost(1_000_000) == 6.60
    assert _build_flow("claude-sonnet-4")._estimate_cost(1_000_000) == 6.60

    # Opus 4.x: $15 in, $75 out  ->  0.7*15 + 0.3*75 = 33.00
    assert _build_flow("claude-opus-4-7")._estimate_cost(1_000_000) == 33.00
    assert _build_flow("claude-opus-4")._estimate_cost(1_000_000) == 33.00


def test_estimate_cost_preserves_legacy_anthropic_models():
    """Existing Claude 3.x branches remain unchanged."""
    # Claude 3 Haiku: $0.25 in, $1.25 out  ->  0.7*0.25 + 0.3*1.25 = 0.55
    assert _build_flow("claude-3-haiku-20240307")._estimate_cost(1_000_000) == 0.55

    # Claude 3.5 Sonnet: $3 in, $15 out  ->  6.60
    assert _build_flow("claude-3-5-sonnet-20241022")._estimate_cost(1_000_000) == 6.60

    # Claude 3 Opus: $15 in, $75 out  ->  33.00
    assert _build_flow("claude-3-opus-20240229")._estimate_cost(1_000_000) == 33.00


def test_estimate_cost_returns_zero_for_no_tokens():
    """Zero tokens means zero cost (early-return guard)."""
    assert _build_flow("claude-haiku-4-5-20251001")._estimate_cost(0) == 0.0
