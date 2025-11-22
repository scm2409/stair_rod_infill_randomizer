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
        min_rod_length_cm=30.0,
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


def test_random_generator_rods_within_boundary(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParameters
) -> None:
    """
    Test that all generated rods stay completely within the frame boundary.

    Requirement 1.6: Rods remain completely within frame boundaries
    Requirement 1.7: Reject rods extending outside frame
    Requirement 1.8: All points along rod geometry contained within frame
    """
    generator = RandomGenerator()
    infill = generator.generate(simple_frame, simple_params)

    # Verify all rods are within the boundary
    for rod in infill.rods:
        # Check that the rod is within the frame boundary
        assert rod.geometry.within(simple_frame.boundary), (
            f"Rod extends outside frame boundary: {rod.geometry}"
        )

        # Additional check: verify start and end points are within or on boundary
        start_point = rod.start_point
        end_point = rod.end_point

        assert simple_frame.boundary.contains(start_point) or simple_frame.boundary.touches(
            start_point
        ), f"Rod start point outside boundary: {start_point}"

        assert simple_frame.boundary.contains(end_point) or simple_frame.boundary.touches(
            end_point
        ), f"Rod end point outside boundary: {end_point}"


def test_random_generator_even_distribution_across_layers(
    simple_frame: RailingFrame,
) -> None:
    """
    Test that rods are evenly distributed across layers.

    Requirement 6.1.1.10: Distribute rods evenly across layers
    Requirement 6.1.1.11: Max 30% difference between layers
    """
    generator = RandomGenerator()

    # Test with different layer counts
    test_cases = [
        (20, 2),  # 20 rods, 2 layers -> 10 per layer
        (30, 3),  # 30 rods, 3 layers -> 10 per layer
        (25, 2),  # 25 rods, 2 layers -> 13 and 12 (1 rod difference)
        (50, 4),  # 50 rods, 4 layers -> 12-13 per layer
    ]

    for num_rods, num_layers in test_cases:
        params = RandomGeneratorParameters(
            num_rods=num_rods,
            min_rod_length_cm=30.0,
            max_rod_length_cm=150.0,
            max_angle_deviation_deg=30.0,
            num_layers=num_layers,
            min_anchor_distance_cm=5.0,
            max_iterations=100,
            max_duration_sec=5.0,
            infill_weight_per_meter_kg_m=0.3,
        )

        infill = generator.generate(simple_frame, params)

        # Count rods per layer
        rods_per_layer = {layer: 0 for layer in range(1, num_layers + 1)}
        for rod in infill.rods:
            rods_per_layer[rod.layer] += 1

        # Calculate min and max counts
        counts = list(rods_per_layer.values())
        min_count = min(counts)
        max_count = max(counts)

        # Verify even distribution
        # The difference should be at most 30% of total rods generated
        # Note: With strict boundary checks, we might not generate all requested rods
        total_generated = sum(counts)
        max_allowed_difference = int(total_generated * 0.3)
        actual_difference = max_count - min_count

        assert actual_difference <= max_allowed_difference, (
            f"Layer distribution too uneven: {rods_per_layer} (difference: {actual_difference}, max allowed: {max_allowed_difference})"
        )

        # For most cases, the difference should be minimal (0-2 rods)
        # This is a stricter check for typical cases
        # Allow up to 2 rods difference to account for boundary constraints
        assert actual_difference <= 2, (
            f"Expected difference of at most 2 rods, got {actual_difference} for {rods_per_layer}"
        )
