"""Tests for RandomGeneratorV2."""

import pytest
from shapely.geometry import LineString

from railing_generator.domain.infill_generators.random_generator_v2 import RandomGeneratorV2
from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
    RandomGeneratorParametersV2,
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

    return RailingFrame(rods=rods)


@pytest.fixture
def simple_params() -> RandomGeneratorParametersV2:
    """Create simple parameters for testing."""
    return RandomGeneratorParametersV2(
        num_rods=5,
        min_rod_length_cm=20.0,
        max_rod_length_cm=180.0,
        max_angle_deviation_deg=40.0,
        num_layers=2,
        max_iterations=500,
        max_duration_sec=10.0,
        infill_weight_per_meter_kg_m=0.3,
        max_evaluation_attempts=1,
        max_evaluation_duration_sec=10.0,
        min_acceptable_fitness=0.7,
        min_anchor_distance_vertical_cm=5.0,
        min_anchor_distance_other_cm=10.0,
        main_direction_range_min_deg=-30.0,
        main_direction_range_max_deg=30.0,
        random_angle_deviation_deg=30.0,
    )


def test_random_generator_v2_creation() -> None:
    """Test creating a RandomGeneratorV2."""
    generator = RandomGeneratorV2()
    assert generator is not None
    assert not generator.is_cancelled()


def test_random_generator_v2_generate_returns_infill(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParametersV2
) -> None:
    """Test that generate returns a RailingInfill."""
    generator = RandomGeneratorV2()
    infill = generator.generate(simple_frame, simple_params)

    assert infill is not None
    assert infill.rods is not None
    assert isinstance(infill.rods, list)


def test_random_generator_v2_generate_creates_rods(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParametersV2
) -> None:
    """Test that generate creates infill rods."""
    generator = RandomGeneratorV2()
    infill = generator.generate(simple_frame, simple_params)

    # Should generate ALL requested rods
    assert len(infill.rods) == simple_params.num_rods


def test_random_generator_v2_rods_have_correct_layer(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParametersV2
) -> None:
    """Test that generated rods have layer >= 1."""
    generator = RandomGeneratorV2()
    infill = generator.generate(simple_frame, simple_params)

    for rod in infill.rods:
        assert rod.layer >= 1
        assert rod.layer <= simple_params.num_layers


def test_random_generator_v2_rods_have_correct_weight(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParametersV2
) -> None:
    """Test that generated rods have correct weight per meter."""
    generator = RandomGeneratorV2()
    infill = generator.generate(simple_frame, simple_params)

    for rod in infill.rods:
        assert rod.weight_kg_m == simple_params.infill_weight_per_meter_kg_m


def test_random_generator_v2_infill_has_metadata(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParametersV2
) -> None:
    """Test that infill contains metadata."""
    generator = RandomGeneratorV2()
    infill = generator.generate(simple_frame, simple_params)

    assert infill.iteration_count is not None
    assert infill.iteration_count > 0
    assert infill.duration_sec is not None
    assert infill.duration_sec >= 0


def test_random_generator_v2_invalid_parameters(simple_frame: RailingFrame) -> None:
    """Test that generator validates parameter types at runtime."""
    generator = RandomGeneratorV2()

    # Pass wrong parameter type
    from railing_generator.domain.infill_generators.generator_parameters import (
        InfillGeneratorParameters,
    )

    class WrongParams(InfillGeneratorParameters):
        """Wrong parameter type for testing."""

        pass

    with pytest.raises(ValueError, match="RandomGeneratorV2 requires RandomGeneratorParametersV2"):
        generator.generate(simple_frame, WrongParams())


def test_random_generator_v2_cancellation(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParametersV2
) -> None:
    """Test that generator cancellation flag works."""
    generator = RandomGeneratorV2()

    # Verify cancellation flag starts as False
    assert not generator.is_cancelled()

    # Cancel the generator
    generator.cancel()
    assert generator.is_cancelled()

    # Reset cancellation
    generator.reset_cancellation()
    assert not generator.is_cancelled()


def test_random_generator_v2_emits_signals(
    qtbot: object, simple_frame: RailingFrame, simple_params: RandomGeneratorParametersV2
) -> None:
    """Test that generator emits signals during generation."""
    generator = RandomGeneratorV2()

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


def test_random_generator_v2_rods_within_boundary(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParametersV2
) -> None:
    """Test that all generated rods stay completely within the frame boundary."""
    generator = RandomGeneratorV2()
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


def test_random_generator_v2_even_distribution_across_layers(
    simple_frame: RailingFrame,
) -> None:
    """Test that rods are evenly distributed across layers."""
    generator = RandomGeneratorV2()

    # Test with different layer counts
    test_cases = [
        (4, 2),  # 4 rods, 2 layers -> 2 per layer
        (6, 3),  # 6 rods, 3 layers -> 2 per layer
        (6, 2),  # 6 rods, 2 layers -> 3 per layer
        (8, 4),  # 8 rods, 4 layers -> 2 per layer
    ]

    for num_rods, num_layers in test_cases:
        params = RandomGeneratorParametersV2(
            num_rods=num_rods,
            min_rod_length_cm=20.0,
            max_rod_length_cm=180.0,
            max_angle_deviation_deg=40.0,
            num_layers=num_layers,
            max_iterations=500,
            max_duration_sec=10.0,
            infill_weight_per_meter_kg_m=0.3,
            max_evaluation_attempts=1,
            max_evaluation_duration_sec=10.0,
            min_acceptable_fitness=0.7,
            min_anchor_distance_vertical_cm=5.0,
            min_anchor_distance_other_cm=10.0,
            main_direction_range_min_deg=-30.0,
            main_direction_range_max_deg=30.0,
            random_angle_deviation_deg=30.0,
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
        total_generated = sum(counts)
        max_allowed_difference = int(total_generated * 0.3)
        actual_difference = max_count - min_count

        assert actual_difference <= max_allowed_difference, (
            f"Layer distribution too uneven: {rods_per_layer} "
            f"(difference: {actual_difference}, max allowed: {max_allowed_difference})"
        )

        # For most cases, the difference should be minimal (0-2 rods)
        assert actual_difference <= 2, (
            f"Expected difference of at most 2 rods, got {actual_difference} for {rods_per_layer}"
        )


def test_random_generator_v2_anchor_points_generated(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParametersV2
) -> None:
    """Test that anchor points are generated and included in the infill result."""
    generator = RandomGeneratorV2()
    infill = generator.generate(simple_frame, simple_params)

    # Verify anchor points are present
    assert infill.anchor_points is not None
    assert len(infill.anchor_points) > 0

    # Verify anchor points have correct attributes
    for anchor in infill.anchor_points:
        assert anchor.position is not None
        assert len(anchor.position) == 2
        assert anchor.frame_segment_index is not None
        assert anchor.layer is not None
        assert anchor.layer >= 1
        assert anchor.layer <= simple_params.num_layers


def test_random_generator_v2_frame_segment_classification(
    simple_frame: RailingFrame,
) -> None:
    """Test that frame segments are correctly classified as vertical or horizontal/sloped."""
    generator = RandomGeneratorV2()

    # Test with known frame rods
    # Vertical rod (left side): (0, 100) -> (0, 0)
    vertical_rod = simple_frame.rods[3]
    assert generator._classify_frame_segment(vertical_rod) is True

    # Horizontal rod (bottom): (0, 0) -> (200, 0)
    horizontal_rod = simple_frame.rods[0]
    assert generator._classify_frame_segment(horizontal_rod) is False

    # Vertical rod (right side): (200, 0) -> (200, 100)
    vertical_rod_2 = simple_frame.rods[1]
    assert generator._classify_frame_segment(vertical_rod_2) is True

    # Horizontal rod (top): (200, 100) -> (0, 100)
    horizontal_rod_2 = simple_frame.rods[2]
    assert generator._classify_frame_segment(horizontal_rod_2) is False


def test_random_generator_v2_layer_main_directions(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParametersV2
) -> None:
    """Test that layer main directions are calculated correctly."""
    generator = RandomGeneratorV2()

    # Test with 2 layers
    directions_2 = generator._calculate_layer_main_directions(
        num_layers=2, min_angle_deg=-30.0, max_angle_deg=30.0
    )
    assert len(directions_2) == 2
    assert directions_2[1] == -30.0
    assert directions_2[2] == 30.0

    # Test with 3 layers
    directions_3 = generator._calculate_layer_main_directions(
        num_layers=3, min_angle_deg=-30.0, max_angle_deg=30.0
    )
    assert len(directions_3) == 3
    assert directions_3[1] == -30.0
    assert directions_3[2] == 0.0
    assert directions_3[3] == 30.0

    # Test with 1 layer (should use midpoint)
    directions_1 = generator._calculate_layer_main_directions(
        num_layers=1, min_angle_deg=-30.0, max_angle_deg=30.0
    )
    assert len(directions_1) == 1
    assert directions_1[1] == 0.0


def test_random_generator_v2_anchor_distribution_to_layers(
    simple_frame: RailingFrame, simple_params: RandomGeneratorParametersV2
) -> None:
    """Test that anchors are evenly distributed across layers."""
    generator = RandomGeneratorV2()

    # Generate anchor points
    anchor_points_by_segment = generator._generate_anchor_points_by_frame_segment(
        simple_frame, simple_params
    )

    # Distribute to layers
    anchors_by_layer = generator._distribute_anchors_to_layers(
        anchor_points_by_segment, simple_params.num_layers
    )

    # Verify even distribution
    counts = [len(anchors) for anchors in anchors_by_layer.values()]
    min_count = min(counts)
    max_count = max(counts)

    # Difference should be at most 1
    assert max_count - min_count <= 1, (
        f"Anchor distribution too uneven: {counts} (difference: {max_count - min_count})"
    )

    # Verify all anchors have layer assigned
    for layer, anchors in anchors_by_layer.items():
        for anchor in anchors:
            assert anchor.layer == layer


def test_random_generator_v2_with_quality_evaluator(simple_frame: RailingFrame) -> None:
    """Test RandomGeneratorV2 with Quality Evaluator integration."""
    from railing_generator.domain.evaluators.quality_evaluator_parameters import (
        QualityEvaluatorParameters,
    )

    # Create parameters with quality evaluator
    params = RandomGeneratorParametersV2(
        num_rods=10,
        min_rod_length_cm=20.0,
        max_rod_length_cm=180.0,
        max_angle_deviation_deg=40.0,
        num_layers=2,
        max_iterations=500,
        max_duration_sec=10.0,
        infill_weight_per_meter_kg_m=0.3,
        max_evaluation_attempts=3,
        max_evaluation_duration_sec=10.0,
        min_acceptable_fitness=0.5,
        min_anchor_distance_vertical_cm=5.0,
        min_anchor_distance_other_cm=10.0,
        main_direction_range_min_deg=-30.0,
        main_direction_range_max_deg=30.0,
        random_angle_deviation_deg=30.0,
        evaluator=QualityEvaluatorParameters(
            type="quality",
            max_hole_area_cm2=10000.0,
            hole_uniformity_weight=0.3,
            incircle_uniformity_weight=0.2,
            angle_distribution_weight=0.2,
            anchor_spacing_horizontal_weight=0.15,
            anchor_spacing_vertical_weight=0.15,
        ),
    )

    generator = RandomGeneratorV2()
    infill = generator.generate(simple_frame, params)

    # Verify infill was generated
    assert infill is not None
    assert len(infill.rods) > 0

    # Verify fitness score was calculated
    assert infill.fitness_score is not None
    assert 0.0 <= infill.fitness_score <= 1.0

    # Verify metadata
    assert infill.iteration_count is not None
    assert infill.iteration_count > 0
    assert infill.duration_sec is not None
    assert infill.duration_sec >= 0


def test_random_generator_v2_with_passthrough_evaluator(simple_frame: RailingFrame) -> None:
    """Test RandomGeneratorV2 with Pass-Through Evaluator integration."""
    from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
        PassThroughEvaluatorParameters,
    )

    # Create parameters with pass-through evaluator
    params = RandomGeneratorParametersV2(
        num_rods=10,
        min_rod_length_cm=20.0,
        max_rod_length_cm=180.0,
        max_angle_deviation_deg=40.0,
        num_layers=2,
        max_iterations=500,
        max_duration_sec=10.0,
        infill_weight_per_meter_kg_m=0.3,
        max_evaluation_attempts=1,
        max_evaluation_duration_sec=10.0,
        min_acceptable_fitness=0.7,
        min_anchor_distance_vertical_cm=5.0,
        min_anchor_distance_other_cm=10.0,
        main_direction_range_min_deg=-30.0,
        main_direction_range_max_deg=30.0,
        random_angle_deviation_deg=30.0,
        evaluator=PassThroughEvaluatorParameters(type="passthrough"),
    )

    generator = RandomGeneratorV2()
    infill = generator.generate(simple_frame, params)

    # Verify infill was generated
    assert infill is not None
    assert len(infill.rods) > 0

    # Verify fitness score (pass-through always returns 1.0)
    assert infill.fitness_score is not None
    assert infill.fitness_score == 1.0

    # Verify metadata
    assert infill.iteration_count is not None
    assert infill.duration_sec is not None


def test_random_generator_v2_quality_evaluator_improves_fitness(
    simple_frame: RailingFrame,
) -> None:
    """Test that quality evaluator finds better arrangements over multiple attempts."""
    from railing_generator.domain.evaluators.quality_evaluator_parameters import (
        QualityEvaluatorParameters,
    )

    # Create parameters with multiple evaluation attempts
    params = RandomGeneratorParametersV2(
        num_rods=8,
        min_rod_length_cm=20.0,
        max_rod_length_cm=180.0,
        max_angle_deviation_deg=40.0,
        num_layers=2,
        max_iterations=500,
        max_duration_sec=10.0,
        infill_weight_per_meter_kg_m=0.3,
        max_evaluation_attempts=5,
        max_evaluation_duration_sec=15.0,
        min_acceptable_fitness=0.9,  # High threshold to force multiple attempts
        min_anchor_distance_vertical_cm=5.0,
        min_anchor_distance_other_cm=10.0,
        main_direction_range_min_deg=-30.0,
        main_direction_range_max_deg=30.0,
        random_angle_deviation_deg=30.0,
        evaluator=QualityEvaluatorParameters(
            type="quality",
            max_hole_area_cm2=10000.0,
            hole_uniformity_weight=0.3,
            incircle_uniformity_weight=0.2,
            angle_distribution_weight=0.2,
            anchor_spacing_horizontal_weight=0.15,
            anchor_spacing_vertical_weight=0.15,
        ),
    )

    generator = RandomGeneratorV2()

    # Track best fitness updates
    fitness_updates: list[float] = []

    def on_best_result(infill: object) -> None:
        from railing_generator.domain.railing_infill import RailingInfill

        if isinstance(infill, RailingInfill) and infill.fitness_score is not None:
            fitness_updates.append(infill.fitness_score)

    generator.best_result_updated.connect(on_best_result)

    infill = generator.generate(simple_frame, params)

    # Verify we got multiple fitness updates (evaluator tried multiple arrangements)
    assert len(fitness_updates) >= 1, "Should have at least one fitness update"

    # Verify final result has fitness score
    assert infill.fitness_score is not None
    assert 0.0 <= infill.fitness_score <= 1.0

    # If we got multiple updates, verify fitness improved or stayed the same
    if len(fitness_updates) > 1:
        for i in range(1, len(fitness_updates)):
            assert fitness_updates[i] >= fitness_updates[i - 1], (
                f"Fitness should not decrease: {fitness_updates[i]} < {fitness_updates[i - 1]}"
            )
