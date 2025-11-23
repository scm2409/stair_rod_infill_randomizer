"""Integration tests for RandomGeneratorV2 with nested evaluator parameters."""

import pytest

from railing_generator.domain.evaluators.evaluator_factory import EvaluatorFactory
from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
    PassThroughEvaluatorParameters,
)
from railing_generator.domain.infill_generators.random_generator_v2 import RandomGeneratorV2
from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
    RandomGeneratorParametersV2,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.rod import Rod
from shapely.geometry import LineString


@pytest.fixture
def simple_rectangular_frame() -> RailingFrame:
    """Create a simple rectangular frame for testing."""
    # Create frame rods (4 sides) for a 200cm x 150cm rectangular frame
    frame_rods = [
        Rod(
            geometry=LineString([(0, 0), (200, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(200, 0), (200, 150)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(200, 150), (0, 150)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(0, 150), (0, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
    ]

    # Boundary is computed from rods
    return RailingFrame(rods=frame_rods)


@pytest.fixture
def v2_parameters() -> RandomGeneratorParametersV2:
    """Create test parameters for RandomGeneratorV2 with nested evaluator."""
    return RandomGeneratorParametersV2(
        num_rods=10,
        min_rod_length_cm=30.0,
        max_rod_length_cm=150.0,
        max_angle_deviation_deg=30.0,
        num_layers=2,
        max_iterations=500,
        max_duration_sec=5.0,
        infill_weight_per_meter_kg_m=0.3,
        min_anchor_distance_vertical_cm=10.0,
        min_anchor_distance_other_cm=10.0,
        main_direction_range_min_deg=-20.0,
        main_direction_range_max_deg=20.0,
        random_angle_deviation_deg=15.0,
        evaluator=PassThroughEvaluatorParameters(),  # Nested evaluator params
    )


def test_v2_with_nested_passthrough_evaluator(
    simple_rectangular_frame: RailingFrame, v2_parameters: RandomGeneratorParametersV2
) -> None:
    """Test RandomGeneratorV2 creates evaluator from nested parameters."""
    # Create generator
    generator = RandomGeneratorV2()

    # Generate infill - generator creates evaluator from params.evaluator
    infill = generator.generate(simple_rectangular_frame, v2_parameters)

    # Verify infill was created
    assert infill is not None
    assert len(infill.rods) > 0

    # Verify all rods are within the frame boundary
    for rod in infill.rods:
        assert rod.geometry.within(simple_rectangular_frame.boundary)

    # Verify rods are in correct layers (1 or 2)
    for rod in infill.rods:
        assert rod.layer in [1, 2]

    # Verify evaluator was created and stored
    assert generator.evaluator is not None
    assert generator.evaluator.__class__.__name__ == "PassThroughEvaluator"


def test_v2_nested_evaluator_in_parameters(v2_parameters: RandomGeneratorParametersV2) -> None:
    """Test that evaluator is nested in V2 parameters."""
    assert hasattr(v2_parameters, "evaluator")
    assert isinstance(v2_parameters.evaluator, PassThroughEvaluatorParameters)
    assert v2_parameters.evaluator.type == "passthrough"


def test_v2_parameters_from_defaults() -> None:
    """Test creating V2 parameters from defaults includes nested evaluator."""
    from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
        RandomGeneratorDefaultsV2,
    )

    defaults = RandomGeneratorDefaultsV2()
    params = RandomGeneratorParametersV2.from_defaults(defaults)

    assert hasattr(params, "evaluator")
    assert isinstance(params.evaluator, PassThroughEvaluatorParameters)
    assert params.evaluator.type == "passthrough"


def test_v2_creates_evaluator_automatically(
    simple_rectangular_frame: RailingFrame, v2_parameters: RandomGeneratorParametersV2
) -> None:
    """Test that V2 automatically creates evaluator from nested params."""
    generator = RandomGeneratorV2()

    # Generate - evaluator parameter is ignored, generator uses params.evaluator
    infill = generator.generate(simple_rectangular_frame, v2_parameters)

    # Verify infill was created
    assert infill is not None
    assert len(infill.rods) > 0

    # Verify evaluator was created from nested params
    assert generator.evaluator is not None


def test_evaluator_factory_creates_from_params() -> None:
    """Test that EvaluatorFactory creates evaluator from parameter object."""
    params = PassThroughEvaluatorParameters()
    evaluator = EvaluatorFactory.create_evaluator(params)

    assert evaluator is not None
    assert evaluator.__class__.__name__ == "PassThroughEvaluator"


def test_evaluator_factory_rejects_unknown_param_type() -> None:
    """Test that EvaluatorFactory rejects unknown parameter types."""
    from pydantic import BaseModel

    class UnknownEvaluatorParameters(BaseModel):
        type: str = "unknown"

    unknown_params = UnknownEvaluatorParameters()

    with pytest.raises(ValueError, match="Unknown evaluator parameter type"):
        EvaluatorFactory.create_evaluator(unknown_params)  # type: ignore[arg-type]


def test_pydantic_discriminated_union() -> None:
    """Test that Pydantic correctly handles discriminated union for evaluator params."""
    # Test with dict (simulates JSON deserialization)
    params_dict = {
        "num_rods": 10,
        "min_rod_length_cm": 30.0,
        "max_rod_length_cm": 150.0,
        "max_angle_deviation_deg": 30.0,
        "num_layers": 2,
        "max_iterations": 500,
        "max_duration_sec": 5.0,
        "infill_weight_per_meter_kg_m": 0.3,
        "min_anchor_distance_vertical_cm": 10.0,
        "min_anchor_distance_other_cm": 10.0,
        "main_direction_range_min_deg": -20.0,
        "main_direction_range_max_deg": 20.0,
        "random_angle_deviation_deg": 15.0,
        "evaluator": {"type": "passthrough"},  # Discriminator field
    }

    # Pydantic should automatically select PassThroughEvaluatorParameters
    params = RandomGeneratorParametersV2.model_validate(params_dict)

    assert isinstance(params.evaluator, PassThroughEvaluatorParameters)
    assert params.evaluator.type == "passthrough"
