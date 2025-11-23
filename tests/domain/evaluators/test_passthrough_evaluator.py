"""Tests for Pass-Through Evaluator."""

import pytest
from shapely.geometry import LineString

from railing_generator.domain.evaluators.passthrough_evaluator import PassThroughEvaluator
from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
    PassThroughEvaluatorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod


@pytest.fixture
def passthrough_params() -> PassThroughEvaluatorParameters:
    """Create Pass-Through Evaluator parameters."""
    return PassThroughEvaluatorParameters()


@pytest.fixture
def passthrough_evaluator(
    passthrough_params: PassThroughEvaluatorParameters,
) -> PassThroughEvaluator:
    """Create Pass-Through Evaluator instance."""
    return PassThroughEvaluator(passthrough_params)


@pytest.fixture
def sample_frame() -> RailingFrame:
    """Create a simple rectangular frame for testing."""
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
    return RailingFrame(rods=frame_rods)


@pytest.fixture
def sample_infill() -> RailingInfill:
    """Create a simple infill arrangement for testing."""
    infill_rods = [
        Rod(
            geometry=LineString([(25, 0), (25, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        ),
        Rod(
            geometry=LineString([(50, 0), (50, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        ),
        Rod(
            geometry=LineString([(75, 0), (75, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        ),
    ]
    return RailingInfill(rods=infill_rods)


def test_passthrough_evaluator_initialization(
    passthrough_params: PassThroughEvaluatorParameters,
) -> None:
    """Test Pass-Through Evaluator initialization."""
    evaluator = PassThroughEvaluator(passthrough_params)
    assert evaluator.params == passthrough_params


def test_passthrough_evaluator_evaluate_returns_one(
    passthrough_evaluator: PassThroughEvaluator,
    sample_infill: RailingInfill,
    sample_frame: RailingFrame,
) -> None:
    """Test that evaluate() always returns 1.0."""
    fitness = passthrough_evaluator.evaluate(sample_infill, sample_frame)
    assert fitness == 1.0


def test_passthrough_evaluator_is_acceptable_returns_true(
    passthrough_evaluator: PassThroughEvaluator,
    sample_infill: RailingInfill,
    sample_frame: RailingFrame,
) -> None:
    """Test that is_acceptable() always returns True."""
    acceptable = passthrough_evaluator.is_acceptable(sample_infill, sample_frame)
    assert acceptable is True


def test_passthrough_evaluator_with_empty_infill(
    passthrough_evaluator: PassThroughEvaluator, sample_frame: RailingFrame
) -> None:
    """Test evaluator with empty infill arrangement."""
    empty_infill = RailingInfill(rods=[])

    fitness = passthrough_evaluator.evaluate(empty_infill, sample_frame)
    assert fitness == 1.0

    acceptable = passthrough_evaluator.is_acceptable(empty_infill, sample_frame)
    assert acceptable is True


def test_passthrough_evaluator_with_complex_infill(
    passthrough_evaluator: PassThroughEvaluator, sample_frame: RailingFrame
) -> None:
    """Test evaluator with complex infill arrangement (multiple layers)."""
    complex_infill_rods = [
        # Layer 1 - vertical rods
        Rod(
            geometry=LineString([(20, 0), (20, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        ),
        Rod(
            geometry=LineString([(40, 0), (40, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        ),
        # Layer 2 - diagonal rods
        Rod(
            geometry=LineString([(0, 0), (100, 100)]),
            start_cut_angle_deg=45.0,
            end_cut_angle_deg=45.0,
            weight_kg_m=0.3,
            layer=2,
        ),
        Rod(
            geometry=LineString([(100, 0), (0, 100)]),
            start_cut_angle_deg=-45.0,
            end_cut_angle_deg=-45.0,
            weight_kg_m=0.3,
            layer=2,
        ),
    ]
    complex_infill = RailingInfill(rods=complex_infill_rods)

    fitness = passthrough_evaluator.evaluate(complex_infill, sample_frame)
    assert fitness == 1.0

    acceptable = passthrough_evaluator.is_acceptable(complex_infill, sample_frame)
    assert acceptable is True


def test_passthrough_evaluator_parameters_validation() -> None:
    """Test that PassThroughEvaluatorParameters can be created and validated."""
    # Should create successfully with no parameters
    params = PassThroughEvaluatorParameters()
    assert params is not None

    # Should serialize with type discriminator
    params_dict = params.model_dump()
    assert params_dict == {"type": "passthrough"}

    # Should deserialize from dict with type
    params_from_dict = PassThroughEvaluatorParameters.model_validate({"type": "passthrough"})
    assert params_from_dict is not None
    assert params_from_dict.type == "passthrough"

    # Should also work with empty dict (type has default)
    params_from_empty = PassThroughEvaluatorParameters.model_validate({})
    assert params_from_empty is not None
    assert params_from_empty.type == "passthrough"


def test_passthrough_evaluator_accepts_incomplete_infill(
    passthrough_evaluator: PassThroughEvaluator, sample_frame: RailingFrame
) -> None:
    """Test that PassThroughEvaluator accepts incomplete infills."""
    # Create an incomplete infill (is_complete=False)
    incomplete_infill = RailingInfill(
        rods=[
            Rod(
                geometry=LineString([(25, 0), (25, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
        ],
        is_complete=False,
    )

    # PassThroughEvaluator should still accept incomplete infills
    fitness = passthrough_evaluator.evaluate(incomplete_infill, sample_frame)
    assert fitness == 1.0

    acceptable = passthrough_evaluator.is_acceptable(incomplete_infill, sample_frame)
    assert acceptable is True
