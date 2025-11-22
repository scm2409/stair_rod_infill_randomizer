"""Tests for RandomGenerator."""
import pytest
from shapely.geometry import LineString

from railing_generator.domain.infill_generators.random_generator import RandomGenerator
from railing_generator.domain.infill_generators.random_generator_parameters import (
    RandomGeneratorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.rod import Rod


@pytest.fixture
def simple_frame() -> RailingFrame:
    """Create a simple rectangular frame for testing."""
    # Create a 200x100 cm rectangular frame with closed rods
    # Frame rods must form a closed boundary
    rods = [
        Rod(
            geometry=LineString([(0, 0), (200, 0)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(200, 0), (200, 100)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(200, 100), (0, 100)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(0, 100), (0, 0)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
    ]

    # RailingFrame only takes rods, boundary is computed
    return RailingFrame(rods=rods)


@pytest.fixture
def simple_params() -> RandomGeneratorParameters:
    """Create simple parameters for testing."""
    return RandomGeneratorParameters(
        num_rods=10,
        max_rod_length_cm=150.0,
        max_angle_deviation_deg=30.0,
        num_layers=2,
        min_anchor_distance_cm=5.0,
        max_iterations=100,
        max_duration_sec=5.0,
        infill_weight_per_meter_kg_m=0.3,
    )


def test_random_generator_creation() -> None:
    """Test creating a RandomGenerator."""
    generator = RandomGenerator()
    assert generator is not None
    assert not generator.is_cancelled()


def test_random_generator_generate_returns_infill(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParameters
) -> None:
    """Test that generate returns a RailingInfill."""
    generator = RandomGenerator()
    infill = generator.generate(simple_frame, simple_params)

    assert infill is not None
    assert infill.rods is not None
    assert isinstance(infill.rods, list)


def test_random_generator_generate_creates_rods(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParameters
) -> None:
    """Test that generate creates infill rods."""
    generator = RandomGenerator()
    infill = generator.generate(simple_frame, simple_params)

    # Should generate at least some rods (at least 50% of requested)
    assert len(infill.rods) >= simple_params.num_rods * 0.5


def test_random_generator_rods_have_correct_layer(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParameters
) -> None:
    """Test that generated rods have layer >= 1."""
    generator = RandomGenerator()
    infill = generator.generate(simple_frame, simple_params)

    for rod in infill.rods:
        assert rod.layer >= 1
        assert rod.layer <= simple_params.num_layers


def test_random_generator_rods_have_correct_weight(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParameters
) -> None:
    """Test that generated rods have correct weight per meter."""
    generator = RandomGenerator()
    infill = generator.generate(simple_frame, simple_params)

    for rod in infill.rods:
        assert rod.weight_kg_m == simple_params.infill_weight_per_meter_kg_m


def test_random_generator_infill_has_metadata(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParameters
) -> None:
    """Test that infill contains metadata."""
    generator = RandomGenerator()
    infill = generator.generate(simple_frame, simple_params)

    assert infill.iteration_count is not None
    assert infill.iteration_count > 0
    assert infill.duration_sec is not None
    assert infill.duration_sec >= 0


def test_random_generator_invalid_parameters(simple_frame: RailingFrame) -> None:
    """Test that generator validates parameter types at runtime."""
    generator = RandomGenerator()

    # Pass wrong parameter type (different InfillGeneratorParameters subclass)
    from railing_generator.domain.infill_generators.generator_parameters import (
        InfillGeneratorParameters,
    )

    class WrongParams(InfillGeneratorParameters):
        """Wrong parameter type for testing."""

        pass

    with pytest.raises(ValueError, match="RandomGenerator requires RandomGeneratorParameters"):
        generator.generate(simple_frame, WrongParams())


def test_random_generator_cancellation(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParameters
) -> None:
    """Test that generator cancellation flag works."""
    generator = RandomGenerator()

    # Verify cancellation flag starts as False
    assert not generator.is_cancelled()

    # Cancel the generator
    generator.cancel()
    assert generator.is_cancelled()

    # Reset cancellation
    generator.reset_cancellation()
    assert not generator.is_cancelled()

    # Note: Testing actual cancellation during generation is difficult
    # because the generator may succeed on the first iteration.
    # The cancellation mechanism is tested in the Generator base class tests.


def test_random_generator_emits_signals(
    qtbot: object, simple_frame: RailingFrame, simple_params: RandomGeneratorParameters
) -> None:
    """Test that generator emits signals during generation."""
    generator = RandomGenerator()

    # Track signal emissions
    progress_emitted = False
    best_result_emitted = False
    completed_emitted = False

    def on_progress(data: dict[str, object]) -> None:
        nonlocal progress_emitted
        progress_emitted = True

    def on_best_result(infill: object) -> None:
        nonlocal best_result_emitted
        best_result_emitted = True

    def on_completed(infill: object) -> None:
        nonlocal completed_emitted
        completed_emitted = True

    generator.progress_updated.connect(on_progress)
    generator.best_result_updated.connect(on_best_result)
    generator.generation_completed.connect(on_completed)

    # Generate
    generator.generate(simple_frame, simple_params)

    # Verify signals were emitted
    assert progress_emitted, "progress_updated signal not emitted"
    assert best_result_emitted, "best_result_updated signal not emitted"
    assert completed_emitted, "generation_completed signal not emitted"
