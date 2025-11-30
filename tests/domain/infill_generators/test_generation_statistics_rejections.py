"""Tests for evaluator rejection tracking in GenerationStatistics."""

from railing_generator.domain.infill_generators.generation_statistics import (
    GenerationStatistics,
)


def test_statistics_tracks_evaluator_rejections() -> None:
    """Test that statistics correctly tracks evaluator rejection counts."""
    stats = GenerationStatistics()

    # Simulate multiple rejections
    stats.evaluator_rejections_total = 10
    stats.evaluator_rejections_incomplete = 3
    stats.evaluator_rejections_hole_too_large = 5
    stats.evaluator_rejections_hole_too_small = 2

    # Verify counts
    assert stats.evaluator_rejections_total == 10
    assert stats.evaluator_rejections_incomplete == 3
    assert stats.evaluator_rejections_hole_too_large == 5
    assert stats.evaluator_rejections_hole_too_small == 2


def test_statistics_string_includes_rejection_details() -> None:
    """Test that __str__ includes detailed rejection information."""
    stats = GenerationStatistics(
        rods_created=18,
        rods_requested=20,
        evaluator_rejections_total=5,
        evaluator_rejections_incomplete=2,
        evaluator_rejections_hole_too_large=2,
        evaluator_rejections_hole_too_small=1,
    )

    output = str(stats)

    # Check that rejection details are in output
    assert "Evaluator Rejections:" in output
    assert "Total arrangements rejected: 5" in output
    assert "Incomplete: 2" in output
    assert "Hole too large: 2" in output
    assert "Hole too small: 1" in output


def test_statistics_accumulates_multiple_criteria_per_arrangement() -> None:
    """Test that statistics can accumulate multiple rejection criteria from one arrangement."""
    stats = GenerationStatistics()

    # Simulate an arrangement that was incomplete AND had 3 holes too large
    stats.evaluator_rejections_total += 1
    stats.evaluator_rejections_incomplete += 1
    stats.evaluator_rejections_hole_too_large += 3

    assert stats.evaluator_rejections_total == 1  # One arrangement rejected
    assert stats.evaluator_rejections_incomplete == 1
    assert stats.evaluator_rejections_hole_too_large == 3  # But 3 holes were too large
