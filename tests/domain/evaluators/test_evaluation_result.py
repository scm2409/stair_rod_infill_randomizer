"""Tests for EvaluationResult and RejectionReasons."""

from railing_generator.domain.evaluators.evaluation_result import (
    EvaluationResult,
    RejectionReasons,
)


def test_rejection_reasons_empty() -> None:
    """Test empty rejection reasons."""
    reasons = RejectionReasons()

    assert reasons.total == 0
    assert reasons.has_rejections is False
    assert str(reasons) == "none"


def test_rejection_reasons_with_counts() -> None:
    """Test rejection reasons with various counts."""
    reasons = RejectionReasons(incomplete=1, hole_too_large=3, hole_too_small=2)

    assert reasons.total == 6
    assert reasons.has_rejections is True
    assert "incomplete(1)" in str(reasons)
    assert "hole_too_large(3)" in str(reasons)
    assert "hole_too_small(2)" in str(reasons)


def test_evaluation_result_accepted() -> None:
    """Test creating an accepted result."""
    result = EvaluationResult.accepted()

    assert result.is_acceptable is True
    assert result.rejection_reasons.total == 0


def test_evaluation_result_rejected() -> None:
    """Test creating a rejected result with reasons."""
    reasons = RejectionReasons(hole_too_large=2)
    result = EvaluationResult.rejected(reasons)

    assert result.is_acceptable is False
    assert result.rejection_reasons.hole_too_large == 2
    assert result.rejection_reasons.total == 2
