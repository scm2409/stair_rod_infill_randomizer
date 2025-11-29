"""Integration test for incomplete infill handling across evaluators."""

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


def test_incomplete_infill_flow() -> None:
    """Test that incomplete infills are handled correctly by different evaluators."""
    # Create a simple frame
    frame_rods = [
        Rod(
            geometry=LineString([(0, 0), (100, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(100, 0), (100, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(100, 100), (0, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(0, 100), (0, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
    ]
    frame = RailingFrame(rods=frame_rods)

    # Create an incomplete infill
    incomplete_infill = RailingInfill(
        rods=[
            Rod(
                geometry=LineString([(50, 0), (50, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
        ],
        is_complete=False,
    )

    # Create a complete infill
    complete_infill = RailingInfill(
        rods=[
            Rod(
                geometry=LineString([(50, 0), (50, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
        ],
        is_complete=True,
    )

    # Test with QualityEvaluator
    quality_params = QualityEvaluatorParameters(
        max_hole_area_cm2=10000.0,
        min_hole_area_cm2=10.0,
        hole_uniformity_weight=0.3,
        incircle_uniformity_weight=0.2,
        angle_distribution_weight=0.2,
        anchor_spacing_horizontal_weight=0.15,
        anchor_spacing_vertical_weight=0.15,
    )
    quality_evaluator = QualityEvaluator(quality_params)

    # QualityEvaluator should reject incomplete infills
    assert quality_evaluator.is_acceptable(incomplete_infill, frame) is False
    # QualityEvaluator should accept complete infills
    assert quality_evaluator.is_acceptable(complete_infill, frame) is True

    # Test with PassthroughEvaluator
    passthrough_params = PassThroughEvaluatorParameters()
    passthrough_evaluator = PassThroughEvaluator(passthrough_params)

    # PassthroughEvaluator should accept both incomplete and complete infills
    assert passthrough_evaluator.is_acceptable(incomplete_infill, frame) is True
    assert passthrough_evaluator.is_acceptable(complete_infill, frame) is True


def test_infill_is_complete_default() -> None:
    """Test that RailingInfill.is_complete defaults to True."""
    infill = RailingInfill(
        rods=[
            Rod(
                geometry=LineString([(0, 0), (100, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
        ]
    )

    # Default should be True (complete)
    assert infill.is_complete is True


def test_infill_is_complete_explicit() -> None:
    """Test that RailingInfill.is_complete can be set explicitly."""
    # Explicitly incomplete
    incomplete_infill = RailingInfill(
        rods=[
            Rod(
                geometry=LineString([(0, 0), (100, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
        ],
        is_complete=False,
    )
    assert incomplete_infill.is_complete is False

    # Explicitly complete
    complete_infill = RailingInfill(
        rods=[
            Rod(
                geometry=LineString([(0, 0), (100, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
        ],
        is_complete=True,
    )
    assert complete_infill.is_complete is True
