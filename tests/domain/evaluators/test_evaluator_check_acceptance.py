"""Tests for evaluator check_acceptance method."""

import pytest
from shapely.geometry import LineString

from railing_generator.domain.evaluators.passthrough_evaluator import PassThroughEvaluator
from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
    PassThroughEvaluatorParameters,
)
from railing_generator.domain.evaluators.quality_evaluator import QualityEvaluator
from railing_generator.domain.evaluators.quality_evaluator_parameters import (
    QualityEvaluatorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod


@pytest.fixture
def simple_frame() -> RailingFrame:
    """Create a simple rectangular frame."""
    frame_rods = [
        Rod(
            geometry=LineString([(0, 0), (0, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=1.0,
            layer=0,
        ),
        Rod(
            geometry=LineString([(0, 100), (100, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=1.0,
            layer=0,
        ),
        Rod(
            geometry=LineString([(100, 100), (100, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=1.0,
            layer=0,
        ),
        Rod(
            geometry=LineString([(100, 0), (0, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=1.0,
            layer=0,
        ),
    ]
    return RailingFrame(rods=frame_rods)


def test_passthrough_evaluator_check_acceptance_always_accepts(
    simple_frame: RailingFrame,
) -> None:
    """Test that PassThroughEvaluator.check_acceptance() always returns accepted."""
    evaluator = PassThroughEvaluator(PassThroughEvaluatorParameters())

    # Test with complete infill
    complete_infill = RailingInfill(
        rods=[
            Rod(
                geometry=LineString([(10, 0), (10, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=1,
            )
        ],
        is_complete=True,
    )

    result = evaluator.check_acceptance(complete_infill, simple_frame)

    assert result.is_acceptable is True
    assert result.rejection_reasons.total == 0


def test_quality_evaluator_check_acceptance_rejects_incomplete(
    simple_frame: RailingFrame,
) -> None:
    """Test that QualityEvaluator.check_acceptance() rejects incomplete infills with counts."""
    evaluator = QualityEvaluator(
        QualityEvaluatorParameters(
            max_hole_area_cm2=1000.0,
            min_hole_area_cm2=1.0,
            hole_uniformity_weight=0.25,
            incircle_uniformity_weight=0.25,
            angle_distribution_weight=0.25,
            anchor_spacing_horizontal_weight=0.125,
            anchor_spacing_vertical_weight=0.125,
        )
    )

    incomplete_infill = RailingInfill(
        rods=[
            Rod(
                geometry=LineString([(10, 0), (10, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=1,
            )
        ],
        is_complete=False,
    )

    result = evaluator.check_acceptance(incomplete_infill, simple_frame)

    assert result.is_acceptable is False
    assert result.rejection_reasons.incomplete == 1
    # Note: May also have hole size violations, so total >= 1
    assert result.rejection_reasons.total >= 1


def test_quality_evaluator_check_acceptance_rejects_large_hole(
    simple_frame: RailingFrame,
) -> None:
    """Test that QualityEvaluator.check_acceptance() rejects arrangements with large holes."""
    # Create evaluator with small max hole area
    evaluator = QualityEvaluator(
        QualityEvaluatorParameters(
            max_hole_area_cm2=50.0,  # Very small limit
            min_hole_area_cm2=1.0,
            hole_uniformity_weight=0.25,
            incircle_uniformity_weight=0.25,
            angle_distribution_weight=0.25,
            anchor_spacing_horizontal_weight=0.125,
            anchor_spacing_vertical_weight=0.125,
        )
    )

    # Create infill with one rod (creates two holes, both will be large)
    complete_infill = RailingInfill(
        rods=[
            Rod(
                geometry=LineString([(50, 0), (50, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=1,
            )
        ],
        is_complete=True,
    )

    result = evaluator.check_acceptance(complete_infill, simple_frame)

    assert result.is_acceptable is False
    assert result.rejection_reasons.hole_too_large == 2  # Both holes are too large
    assert result.rejection_reasons.total == 2


def test_quality_evaluator_check_acceptance_accepts_valid_arrangement(
    simple_frame: RailingFrame,
) -> None:
    """Test that QualityEvaluator.check_acceptance() accepts valid arrangements."""
    # Create evaluator with large max hole area
    evaluator = QualityEvaluator(
        QualityEvaluatorParameters(
            max_hole_area_cm2=10000.0,  # Very large limit
            min_hole_area_cm2=0.1,  # Very small minimum
            hole_uniformity_weight=0.25,
            incircle_uniformity_weight=0.25,
            angle_distribution_weight=0.25,
            anchor_spacing_horizontal_weight=0.125,
            anchor_spacing_vertical_weight=0.125,
        )
    )

    # Create complete infill with one rod
    complete_infill = RailingInfill(
        rods=[
            Rod(
                geometry=LineString([(50, 0), (50, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=1,
            )
        ],
        is_complete=True,
    )

    result = evaluator.check_acceptance(complete_infill, simple_frame)

    assert result.is_acceptable is True
    assert result.rejection_reasons.total == 0
