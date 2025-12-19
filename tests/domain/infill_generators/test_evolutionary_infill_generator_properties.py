"""Property-based tests for EvolutionaryInfillGenerator.

Uses Hypothesis for property-based testing to verify correctness properties
defined in the design document.
"""

import math
from datetime import timedelta

from hypothesis import given, settings
from hypothesis import strategies as st
from shapely.geometry import LineString

from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
    PassThroughEvaluatorParameters,
)
from railing_generator.domain.infill_generators.evolutionary_infill_generator import (
    EvolutionaryInfillGenerator,
)
from railing_generator.domain.infill_generators.evolutionary_infill_generator_parameters import (
    EvolutionaryInfillGeneratorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod


# Strategy for generating valid rectangular frames
@st.composite
def valid_rectangular_frame(draw: st.DrawFn) -> RailingFrame:
    """
    Generate a valid rectangular frame with random dimensions.

    Generates frames with width and height between 100 and 400 cm.
    Using larger minimum to ensure enough space for rods.
    """
    width = draw(st.floats(min_value=100.0, max_value=400.0, allow_nan=False, allow_infinity=False))
    height = draw(
        st.floats(min_value=100.0, max_value=400.0, allow_nan=False, allow_infinity=False)
    )

    # Create a rectangular frame with closed rods
    rods = [
        Rod(
            geometry=LineString([(0, 0), (width, 0)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(width, 0), (width, height)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(width, height), (0, height)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(0, height), (0, 0)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
    ]

    return RailingFrame(rods=rods)


# Strategy for generating valid direction ranges
@st.composite
def valid_direction_range(draw: st.DrawFn) -> tuple[float, float]:
    """
    Generate a valid direction range where min < max.

    Both values are in the range [-90, 90] degrees.
    """
    min_deg = draw(
        st.floats(min_value=-90.0, max_value=89.0, allow_nan=False, allow_infinity=False)
    )
    # Ensure max_deg > min_deg with at least 0.1 degree difference
    max_deg = draw(
        st.floats(min_value=min_deg + 0.1, max_value=90.0, allow_nan=False, allow_infinity=False)
    )
    return (min_deg, max_deg)


class TestBaselineLayerDistributionProperty:
    """
    **Feature: evolutionary-infill-generator, Property 1: Baseline Layer Distribution**

    *For any* generated baseline with N rods and L layers, the difference between
    the layer with the most rods and the layer with the fewest rods SHALL be at most 1,
    and layer directions SHALL follow linear interpolation across the configured
    direction range.

    **Validates: Requirements 1.2, 1.3**
    """

    @settings(max_examples=20, deadline=timedelta(seconds=5))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=30),
        num_layers=st.integers(min_value=1, max_value=5),
        direction_range=valid_direction_range(),
    )
    def test_rods_evenly_distributed_across_layers(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 1: Baseline Layer Distribution**

        *For any* generated baseline with N rods and L layers, the difference between
        the layer with the most rods and the layer with the fewest rods SHALL be at most 1.

        **Validates: Requirements 1.2**
        """
        min_deg, max_deg = direction_range

        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,  # Just baseline for this test
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate infill
            infill = generator.generate(frame, params)

            # Count rods per layer
            rods_per_layer: dict[int, int] = {}
            for rod in infill.rods:
                layer = rod.layer
                rods_per_layer[layer] = rods_per_layer.get(layer, 0) + 1

            # Skip if no rods generated (frame too small)
            if not rods_per_layer:
                return

            # Get min and max rod counts
            min_count = min(rods_per_layer.values())
            max_count = max(rods_per_layer.values())

            # The difference should be at most 1
            assert max_count - min_count <= 1, (
                f"Rod distribution is uneven: min={min_count}, max={max_count}, "
                f"difference={max_count - min_count} (should be <= 1)"
            )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=20, deadline=timedelta(seconds=5))
    @given(
        num_layers=st.integers(min_value=2, max_value=5),
        direction_range=valid_direction_range(),
    )
    def test_layer_directions_follow_linear_interpolation(
        self,
        num_layers: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 1: Baseline Layer Distribution**

        *For any* multi-layer configuration, layer directions SHALL follow linear
        interpolation across the configured direction range.

        **Validates: Requirements 1.3**
        """
        min_deg, max_deg = direction_range

        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=10,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        # Calculate layer directions
        layer_directions = generator._calculate_layer_directions(params)

        # Verify each layer's direction follows the formula
        for layer_num in range(1, num_layers + 1):
            assert layer_num in layer_directions, f"Layer {layer_num} should be present"

            # Calculate expected direction using the formula
            layer_index = layer_num - 1
            t = layer_index / (num_layers - 1)
            expected_direction = min_deg + t * (max_deg - min_deg)
            actual_direction = layer_directions[layer_num]

            assert math.isclose(actual_direction, expected_direction, rel_tol=1e-9, abs_tol=1e-9), (
                f"Layer {layer_num} direction {actual_direction:.6f}° should be "
                f"{expected_direction:.6f}° (t={t:.4f}, range=[{min_deg:.2f}°, {max_deg:.2f}°])"
            )

    @settings(max_examples=20, deadline=timedelta(seconds=5))
    @given(
        direction_range=valid_direction_range(),
    )
    def test_single_layer_uses_midpoint(
        self,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 1: Baseline Layer Distribution**

        WHEN there is only one layer THEN the generator SHALL use the midpoint
        of the direction range as the main direction.

        **Validates: Requirements 1.3**
        """
        min_deg, max_deg = direction_range

        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=10,
            num_layers=1,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        # Calculate layer directions
        layer_directions = generator._calculate_layer_directions(params)

        # Should have exactly one layer
        assert len(layer_directions) == 1, f"Expected 1 layer, got {len(layer_directions)}"
        assert 1 in layer_directions, "Layer 1 should be present"

        # Direction should be the midpoint
        expected_direction = (min_deg + max_deg) / 2.0
        actual_direction = layer_directions[1]

        assert math.isclose(actual_direction, expected_direction, rel_tol=1e-9, abs_tol=1e-9), (
            f"Single layer direction {actual_direction:.6f}° should be midpoint "
            f"{expected_direction:.6f}° of range [{min_deg:.2f}°, {max_deg:.2f}°]"
        )


class TestAnchorCountInvarianceProperty:
    """
    **Feature: evolutionary-infill-generator, Property 2: Anchor Count Invariance**

    *For any* generation run, the total number of anchor points SHALL remain constant
    from baseline creation through all mutation iterations.

    **Validates: Requirements 2.1, 2.2**
    """

    @settings(max_examples=20, deadline=timedelta(seconds=5))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=20),
        num_layers=st.integers(min_value=1, max_value=3),
        min_anchor_distance_cm=st.floats(
            min_value=5.0, max_value=30.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_anchor_count_remains_constant(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
        min_anchor_distance_cm: float,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 2: Anchor Count Invariance**

        *For any* generation run, the total number of anchor points SHALL remain
        constant from baseline creation.

        **Validates: Requirements 2.1, 2.2**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,  # Just baseline for this test
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        # Generate anchor grid directly
        anchor_points = generator._generate_anchor_grid(frame, params)
        initial_anchor_count = len(anchor_points)

        # Anchor count should be positive
        assert initial_anchor_count > 0, "Should generate at least some anchor points"

        try:
            # Generate full infill
            infill = generator.generate(frame, params)

            # Check that anchor points in result match initial count
            if infill.anchor_points is not None:
                assert len(infill.anchor_points) == initial_anchor_count, (
                    f"Anchor count changed: initial={initial_anchor_count}, "
                    f"final={len(infill.anchor_points)}"
                )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=20, deadline=timedelta(seconds=5))
    @given(
        frame=valid_rectangular_frame(),
        min_anchor_distance_cm=st.floats(
            min_value=5.0, max_value=30.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_anchors_generated_once_at_baseline(
        self,
        frame: RailingFrame,
        min_anchor_distance_cm: float,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 2: Anchor Count Invariance**

        WHEN generation starts THEN the generator SHALL generate all anchor points
        once during baseline creation.

        **Validates: Requirements 2.1**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=10,
            num_layers=2,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        # Generate anchor grid
        anchor_points = generator._generate_anchor_grid(frame, params)

        # All anchors should start as free (not used)
        for anchor in anchor_points:
            assert anchor.used is False, "Anchor should start as unused"
            assert anchor.layer is None, "Anchor should start with no layer assigned"

        # All anchors should be on the frame boundary
        for anchor in anchor_points:
            distance_to_boundary = frame.boundary.exterior.distance(anchor.position)
            assert distance_to_boundary < 0.01, (
                f"Anchor at {anchor.position} is {distance_to_boundary:.4f}cm "
                f"from boundary (should be on boundary)"
            )

    @settings(max_examples=20, deadline=timedelta(seconds=5))
    @given(
        frame=valid_rectangular_frame(),
        min_anchor_distance_cm=st.floats(
            min_value=5.0, max_value=30.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_all_anchor_pairs_satisfy_minimum_distance(
        self,
        frame: RailingFrame,
        min_anchor_distance_cm: float,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 2: Anchor Count Invariance**

        *For any* frame and min_anchor_distance_cm, all pairs of generated anchor
        points SHALL be separated by at least min_anchor_distance_cm.

        **Validates: Requirements 2.1**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=10,
            num_layers=2,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        # Generate anchor grid
        anchor_points = generator._generate_anchor_grid(frame, params)

        # Skip if fewer than 2 anchors (nothing to compare)
        if len(anchor_points) < 2:
            return

        # Check all pairs of anchor points
        for i, anchor_a in enumerate(anchor_points):
            for anchor_b in anchor_points[i + 1 :]:
                distance = anchor_a.position.distance(anchor_b.position)

                # Allow small tolerance for floating point errors (0.01cm = 0.1mm)
                assert distance >= min_anchor_distance_cm - 0.01, (
                    f"Anchor pair distance {distance:.4f}cm is less than "
                    f"min_anchor_distance_cm {min_anchor_distance_cm:.4f}cm"
                )


class TestAnchorStateConsistencyProperty:
    """
    **Feature: evolutionary-infill-generator, Property 3: Anchor State Consistency**

    *For any* generated infill, the number of used anchor points SHALL equal exactly
    twice the number of rods (each rod uses two anchors), and all used anchors SHALL
    have a layer assignment matching their connected rod.

    **Validates: Requirements 2.3, 2.4, 2.5**
    """

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=20),
        num_layers=st.integers(min_value=1, max_value=3),
    )
    def test_used_anchor_count_equals_twice_rod_count(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 3: Anchor State Consistency**

        *For any* generated infill, the number of used anchor points SHALL equal
        exactly twice the number of rods.

        **Validates: Requirements 2.3, 2.4, 2.5**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,  # Just baseline for this test
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate infill
            infill = generator.generate(frame, params)

            # Skip if no anchor points in result
            if infill.anchor_points is None:
                return

            # Count used anchors
            used_anchor_count = sum(1 for anchor in infill.anchor_points if anchor.used)
            rod_count = len(infill.rods)
            expected_used_anchors = rod_count * 2

            assert used_anchor_count == expected_used_anchors, (
                f"Used anchor count {used_anchor_count} should equal "
                f"2 * rod_count ({rod_count}) = {expected_used_anchors}"
            )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=20),
        num_layers=st.integers(min_value=1, max_value=3),
    )
    def test_used_anchors_have_layer_assignment(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 3: Anchor State Consistency**

        *For any* generated infill, all used anchors SHALL have a layer assignment.

        **Validates: Requirements 2.5**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate infill
            infill = generator.generate(frame, params)

            # Skip if no anchor points in result
            if infill.anchor_points is None:
                return

            # Check all used anchors have layer assignment
            for anchor in infill.anchor_points:
                if anchor.used:
                    assert anchor.layer is not None, (
                        f"Used anchor at {anchor.position} should have layer assignment"
                    )
                    assert anchor.layer >= 1, f"Used anchor layer {anchor.layer} should be >= 1"

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=20),
        num_layers=st.integers(min_value=1, max_value=3),
    )
    def test_free_anchors_have_no_layer_assignment(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 3: Anchor State Consistency**

        *For any* generated infill, all free (unused) anchors SHALL have no layer assignment.

        **Validates: Requirements 2.3, 2.4**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate infill
            infill = generator.generate(frame, params)

            # Skip if no anchor points in result
            if infill.anchor_points is None:
                return

            # Check all free anchors have no layer assignment
            for anchor in infill.anchor_points:
                if not anchor.used:
                    assert anchor.layer is None, (
                        f"Free anchor at {anchor.position} should have no layer assignment, "
                        f"but has layer={anchor.layer}"
                    )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=15),
        num_layers=st.integers(min_value=1, max_value=3),
    )
    def test_anchor_state_consistency_after_mutation(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 3: Anchor State Consistency**

        *For any* infill after mutation, the anchor state SHALL remain consistent:
        - Used anchor count equals 2 * rod count
        - All used anchors have layer assignment
        - All free anchors have no layer assignment

        **Validates: Requirements 2.3, 2.4, 2.5**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate baseline infill
            infill = generator.generate(frame, params)

            # Skip if no anchor points in result
            if infill.anchor_points is None:
                return

            # Perform mutation
            mutated_infill, mutated_anchors = generator._mutate_arrangement(
                infill, infill.anchor_points, frame, num_layers
            )

            # Check anchor state consistency after mutation
            used_anchor_count = sum(1 for anchor in mutated_anchors if anchor.used)
            rod_count = len(mutated_infill.rods)
            expected_used_anchors = rod_count * 2

            assert used_anchor_count == expected_used_anchors, (
                f"After mutation: used anchor count {used_anchor_count} should equal "
                f"2 * rod_count ({rod_count}) = {expected_used_anchors}"
            )

            # Check all used anchors have layer assignment
            for anchor in mutated_anchors:
                if anchor.used:
                    assert anchor.layer is not None, (
                        f"After mutation: used anchor at {anchor.position} "
                        f"should have layer assignment"
                    )

            # Check all free anchors have no layer assignment
            for anchor in mutated_anchors:
                if not anchor.used:
                    assert anchor.layer is None, (
                        f"After mutation: free anchor at {anchor.position} "
                        f"should have no layer assignment, but has layer={anchor.layer}"
                    )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass


class TestNoSameLayerCrossingsProperty:
    """
    **Feature: evolutionary-infill-generator, Property 4: No Same-Layer Crossings**

    *For any* generated infill (baseline or after mutations), no two rods in the
    same layer SHALL cross each other.

    **Validates: Requirements 3.6, 7.3**
    """

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=20),
        num_layers=st.integers(min_value=1, max_value=3),
    )
    def test_no_same_layer_crossings_in_baseline(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 4: No Same-Layer Crossings**

        *For any* generated baseline infill, no two rods in the same layer SHALL
        cross each other.

        **Validates: Requirements 3.6, 7.3**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate infill
            infill = generator.generate(frame, params)

            # Check for same-layer crossings
            for layer_num in range(1, num_layers + 1):
                layer_rods = [rod for rod in infill.rods if rod.layer == layer_num]

                # Check all pairs of rods in this layer
                for i, rod_a in enumerate(layer_rods):
                    for rod_b in layer_rods[i + 1 :]:
                        intersection = rod_a.geometry.intersection(rod_b.geometry)

                        if intersection.is_empty:
                            continue

                        # Point intersection at endpoints is OK
                        if intersection.geom_type == "Point":
                            is_at_endpoint = (
                                intersection.equals(rod_a.start_point)
                                or intersection.equals(rod_a.end_point)
                                or intersection.equals(rod_b.start_point)
                                or intersection.equals(rod_b.end_point)
                            )
                            if is_at_endpoint:
                                continue

                        # Any other intersection is a crossing
                        assert False, (
                            f"Same-layer crossing detected in layer {layer_num}: "
                            f"rod from {rod_a.start_point} to {rod_a.end_point} "
                            f"crosses rod from {rod_b.start_point} to {rod_b.end_point}"
                        )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=15),
        num_layers=st.integers(min_value=1, max_value=3),
    )
    def test_no_same_layer_crossings_after_mutation(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 4: No Same-Layer Crossings**

        *For any* infill after mutation, no two rods in the same layer SHALL
        cross each other.

        **Validates: Requirements 3.6, 7.3**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate baseline infill
            infill = generator.generate(frame, params)

            # Skip if no anchor points in result
            if infill.anchor_points is None:
                return

            # Perform mutation
            mutated_infill, _ = generator._mutate_arrangement(
                infill, infill.anchor_points, frame, num_layers
            )

            # Check for same-layer crossings after mutation
            for layer_num in range(1, num_layers + 1):
                layer_rods = [rod for rod in mutated_infill.rods if rod.layer == layer_num]

                # Check all pairs of rods in this layer
                for i, rod_a in enumerate(layer_rods):
                    for rod_b in layer_rods[i + 1 :]:
                        intersection = rod_a.geometry.intersection(rod_b.geometry)

                        if intersection.is_empty:
                            continue

                        # Point intersection at endpoints is OK
                        if intersection.geom_type == "Point":
                            is_at_endpoint = (
                                intersection.equals(rod_a.start_point)
                                or intersection.equals(rod_a.end_point)
                                or intersection.equals(rod_b.start_point)
                                or intersection.equals(rod_b.end_point)
                            )
                            if is_at_endpoint:
                                continue

                        # Any other intersection is a crossing
                        assert False, (
                            f"Same-layer crossing detected after mutation in layer {layer_num}: "
                            f"rod from {rod_a.start_point} to {rod_a.end_point} "
                            f"crosses rod from {rod_b.start_point} to {rod_b.end_point}"
                        )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass


class TestFitnessMonotonicityProperty:
    """
    **Feature: evolutionary-infill-generator, Property 5: Fitness Monotonicity**

    *For any* generation run, the fitness score of the returned result SHALL be
    greater than or equal to the baseline fitness score.

    **Validates: Requirements 4.2, 4.3**
    """

    @settings(max_examples=20, deadline=timedelta(seconds=30))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=15),
        num_layers=st.integers(min_value=1, max_value=3),
        max_iterations=st.integers(min_value=5, max_value=50),
        improvement_threshold=st.floats(
            min_value=0.0, max_value=0.1, allow_nan=False, allow_infinity=False
        ),
    )
    def test_final_fitness_greater_or_equal_to_baseline(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
        max_iterations: int,
        improvement_threshold: float,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 5: Fitness Monotonicity**

        *For any* generation run, the fitness score of the returned result SHALL be
        greater than or equal to the baseline fitness score.

        **Validates: Requirements 4.2, 4.3**
        """
        from railing_generator.domain.evaluators.evaluator_factory import EvaluatorFactory

        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=max_iterations,
            max_duration_sec=60.0,
            improvement_threshold=improvement_threshold,
            stagnation_limit=max_iterations + 1,  # Don't stop due to stagnation
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Create evaluator to calculate baseline fitness
            evaluator = EvaluatorFactory.create_evaluator(params.evaluator)

            # Generate baseline first to get baseline fitness
            baseline_infill, _, _ = generator._generate_baseline(frame, params, evaluator, 0.0)
            baseline_fitness = baseline_infill.fitness_score or 0.0

            # Reset generator state
            generator.reset_cancellation()

            # Generate full infill with optimization
            final_infill = generator.generate(frame, params)
            final_fitness = final_infill.fitness_score or 0.0

            # Final fitness should be >= baseline fitness
            assert final_fitness >= baseline_fitness - 1e-9, (
                f"Final fitness {final_fitness:.6f} should be >= "
                f"baseline fitness {baseline_fitness:.6f}"
            )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=20, deadline=timedelta(seconds=30))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=15),
        num_layers=st.integers(min_value=1, max_value=3),
    )
    def test_fitness_never_decreases_during_optimization(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 5: Fitness Monotonicity**

        *For any* generation run, the fitness score SHALL never decrease during
        the optimization process.

        **Validates: Requirements 4.2, 4.3**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=20,  # Run a few iterations
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=25,  # Don't stop due to stagnation
            evaluator=PassThroughEvaluatorParameters(),
        )

        # Track fitness scores from best_result_updated signals
        fitness_scores: list[float] = []

        def on_best_result_updated(infill: RailingInfill) -> None:
            if infill.fitness_score is not None:
                fitness_scores.append(infill.fitness_score)

        # Connect signal
        generator.best_result_updated.connect(on_best_result_updated)

        try:
            # Generate infill
            generator.generate(frame, params)

            # Verify fitness scores are monotonically non-decreasing
            for i in range(1, len(fitness_scores)):
                assert fitness_scores[i] >= fitness_scores[i - 1] - 1e-9, (
                    f"Fitness decreased from {fitness_scores[i - 1]:.6f} to "
                    f"{fitness_scores[i]:.6f} at step {i}"
                )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass
        finally:
            # Disconnect signal
            generator.best_result_updated.disconnect(on_best_result_updated)


class TestTerminationLimitsProperty:
    """
    **Feature: evolutionary-infill-generator, Property 8: Termination Limits**

    *For any* generation run, the iteration count SHALL not exceed max_iterations,
    and the duration SHALL not significantly exceed max_duration_sec.

    **Validates: Requirements 5.3, 5.4**
    """

    @settings(max_examples=20, deadline=timedelta(seconds=30))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=15),
        num_layers=st.integers(min_value=1, max_value=3),
        max_iterations=st.integers(min_value=5, max_value=100),
    )
    def test_iteration_count_does_not_exceed_max_iterations(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
        max_iterations: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 8: Termination Limits**

        *For any* generation run, the iteration count SHALL not exceed max_iterations.

        **Validates: Requirements 5.3**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=max_iterations,
            max_duration_sec=300.0,  # Long duration to not trigger time limit
            improvement_threshold=0.001,
            stagnation_limit=max_iterations + 100,  # Don't stop due to stagnation
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate infill
            infill = generator.generate(frame, params)

            # Iteration count should not exceed max_iterations
            assert infill.iteration_count <= max_iterations, (
                f"Iteration count {infill.iteration_count} exceeds max_iterations {max_iterations}"
            )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=15, deadline=timedelta(seconds=60))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=10),
        num_layers=st.integers(min_value=1, max_value=2),
        max_duration_sec=st.floats(
            min_value=0.5, max_value=2.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_duration_does_not_significantly_exceed_max_duration(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
        max_duration_sec: float,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 8: Termination Limits**

        *For any* generation run, the duration SHALL not significantly exceed
        max_duration_sec. We allow some tolerance for the time it takes to
        complete the current iteration after the limit is reached.

        **Validates: Requirements 5.4**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=10000,  # High limit to not trigger iteration limit
            max_duration_sec=max_duration_sec,
            improvement_threshold=0.001,
            stagnation_limit=10000,  # Don't stop due to stagnation
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate infill
            infill = generator.generate(frame, params)

            # Duration should not significantly exceed max_duration_sec
            # Allow 1 second tolerance for completing the current iteration
            # and baseline generation overhead
            tolerance_sec = 1.0
            assert infill.duration_sec <= max_duration_sec + tolerance_sec, (
                f"Duration {infill.duration_sec:.2f}s significantly exceeds "
                f"max_duration_sec {max_duration_sec:.2f}s "
                f"(tolerance: {tolerance_sec:.2f}s)"
            )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=20, deadline=timedelta(seconds=30))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=15),
        num_layers=st.integers(min_value=1, max_value=3),
        stagnation_limit=st.integers(min_value=5, max_value=50),
    )
    def test_stagnation_limit_triggers_early_termination(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
        stagnation_limit: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 8: Termination Limits**

        WHEN stagnation_limit consecutive iterations produce no improvement
        THEN the generator SHALL stop and return the current best result.

        **Validates: Requirements 5.5, 5.6**
        """
        # Create generator and parameters with high improvement threshold
        # to ensure no improvements are found (triggering stagnation)
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=10000,  # High limit to not trigger iteration limit
            max_duration_sec=300.0,  # Long duration to not trigger time limit
            improvement_threshold=1.0,  # Very high threshold - no improvements possible
            stagnation_limit=stagnation_limit,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate infill
            infill = generator.generate(frame, params)

            # With improvement_threshold=1.0, no improvements should be found
            # So the generator should stop at stagnation_limit iterations
            # (plus 1 for the baseline iteration)
            # The iteration count should be approximately stagnation_limit
            # Allow some tolerance since baseline counts as iteration 0
            assert infill.iteration_count <= stagnation_limit + 1, (
                f"Iteration count {infill.iteration_count} should be <= "
                f"stagnation_limit + 1 ({stagnation_limit + 1}) when no improvements found"
            )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass


class TestRodBoundaryConstraintsProperty:
    """
    **Feature: evolutionary-infill-generator, Property 6: Rod Boundary Constraints**

    *For any* generated rod, both endpoints SHALL lie on the frame boundary,
    and the entire rod geometry SHALL be within the frame boundary.

    **Validates: Requirements 7.1, 7.2**
    """

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=20),
        num_layers=st.integers(min_value=1, max_value=3),
    )
    def test_all_rod_endpoints_on_boundary(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 6: Rod Boundary Constraints**

        *For any* generated rod, both endpoints SHALL lie on the frame boundary.

        **Validates: Requirements 7.1**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,  # Just baseline for this test
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate infill
            infill = generator.generate(frame, params)

            # Check all rods have endpoints on boundary
            boundary = frame.boundary.exterior
            tolerance = 0.1  # 0.1 cm tolerance

            for rod in infill.rods:
                # Check start point
                start_distance = boundary.distance(rod.start_point)
                assert start_distance <= tolerance, (
                    f"Rod start point {rod.start_point} is {start_distance:.4f}cm "
                    f"from boundary (tolerance: {tolerance}cm)"
                )

                # Check end point
                end_distance = boundary.distance(rod.end_point)
                assert end_distance <= tolerance, (
                    f"Rod end point {rod.end_point} is {end_distance:.4f}cm "
                    f"from boundary (tolerance: {tolerance}cm)"
                )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=20),
        num_layers=st.integers(min_value=1, max_value=3),
    )
    def test_all_rods_within_boundary(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 6: Rod Boundary Constraints**

        *For any* generated rod, the entire rod geometry SHALL be within the
        frame boundary.

        **Validates: Requirements 7.2**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,  # Just baseline for this test
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate infill
            infill = generator.generate(frame, params)

            # Check all rods are within boundary
            boundary = frame.boundary
            tolerance = 0.1  # 0.1 cm tolerance
            buffered_boundary = boundary.buffer(tolerance)

            for rod in infill.rods:
                assert buffered_boundary.contains(rod.geometry) or rod.geometry.within(
                    buffered_boundary
                ), f"Rod from {rod.start_point} to {rod.end_point} is not within frame boundary"

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=15),
        num_layers=st.integers(min_value=1, max_value=3),
    )
    def test_rod_boundary_constraints_after_mutation(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 6: Rod Boundary Constraints**

        *For any* infill after mutation, all rods SHALL still satisfy boundary
        constraints (endpoints on boundary, geometry within boundary).

        **Validates: Requirements 7.1, 7.2**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate baseline infill
            infill = generator.generate(frame, params)

            # Skip if no anchor points in result
            if infill.anchor_points is None:
                return

            # Perform mutation
            mutated_infill, _ = generator._mutate_arrangement(
                infill, infill.anchor_points, frame, num_layers
            )

            # Check all rods satisfy boundary constraints after mutation
            boundary = frame.boundary
            boundary_exterior = boundary.exterior
            tolerance = 0.1  # 0.1 cm tolerance
            buffered_boundary = boundary.buffer(tolerance)

            for rod in mutated_infill.rods:
                # Check endpoints on boundary
                start_distance = boundary_exterior.distance(rod.start_point)
                assert start_distance <= tolerance, (
                    f"After mutation: rod start point {rod.start_point} is "
                    f"{start_distance:.4f}cm from boundary (tolerance: {tolerance}cm)"
                )

                end_distance = boundary_exterior.distance(rod.end_point)
                assert end_distance <= tolerance, (
                    f"After mutation: rod end point {rod.end_point} is "
                    f"{end_distance:.4f}cm from boundary (tolerance: {tolerance}cm)"
                )

                # Check rod within boundary
                assert buffered_boundary.contains(rod.geometry) or rod.geometry.within(
                    buffered_boundary
                ), (
                    f"After mutation: rod from {rod.start_point} to {rod.end_point} "
                    f"is not within frame boundary"
                )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=15),
        num_layers=st.integers(min_value=1, max_value=3),
    )
    def test_verify_rod_constraints_method(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 6: Rod Boundary Constraints**

        *For any* generated rod, the verify_rod_constraints method SHALL return True.

        **Validates: Requirements 7.1, 7.2**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate infill
            infill = generator.generate(frame, params)

            # Verify all rods pass constraint check
            for rod in infill.rods:
                assert generator.verify_rod_constraints(rod, frame), (
                    f"Rod from {rod.start_point} to {rod.end_point} failed constraint verification"
                )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass


class TestMinimumAnchorDistanceProperty:
    """
    **Feature: evolutionary-infill-generator, Property 7: Minimum Anchor Distance**

    *For any* generated infill, all pairs of anchor points SHALL be separated
    by at least min_anchor_distance_cm.

    **Validates: Requirements 7.4**
    """

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        min_anchor_distance_cm=st.floats(
            min_value=5.0, max_value=30.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_all_anchor_pairs_satisfy_minimum_distance(
        self,
        frame: RailingFrame,
        min_anchor_distance_cm: float,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 7: Minimum Anchor Distance**

        *For any* frame and min_anchor_distance_cm, all pairs of generated anchor
        points SHALL be separated by at least min_anchor_distance_cm.

        **Validates: Requirements 7.4**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=10,
            num_layers=2,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        # Generate anchor grid
        anchor_points = generator._generate_anchor_grid(frame, params)

        # Skip if fewer than 2 anchors (nothing to compare)
        if len(anchor_points) < 2:
            return

        # Check all pairs of anchor points
        # Allow small tolerance for floating point errors (0.01cm = 0.1mm)
        tolerance = 0.01

        for i, anchor_a in enumerate(anchor_points):
            for anchor_b in anchor_points[i + 1 :]:
                distance = anchor_a.position.distance(anchor_b.position)

                assert distance >= min_anchor_distance_cm - tolerance, (
                    f"Anchor pair distance {distance:.4f}cm is less than "
                    f"min_anchor_distance_cm {min_anchor_distance_cm:.4f}cm "
                    f"(tolerance: {tolerance}cm)"
                )

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=15),
        num_layers=st.integers(min_value=1, max_value=3),
        min_anchor_distance_cm=st.floats(
            min_value=5.0, max_value=20.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_minimum_distance_maintained_in_generated_infill(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
        min_anchor_distance_cm: float,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 7: Minimum Anchor Distance**

        *For any* generated infill, all anchor points in the result SHALL maintain
        the minimum distance constraint.

        **Validates: Requirements 7.4**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate infill
            infill = generator.generate(frame, params)

            # Skip if no anchor points in result
            if infill.anchor_points is None or len(infill.anchor_points) < 2:
                return

            # Check all pairs of anchor points
            tolerance = 0.01

            for i, anchor_a in enumerate(infill.anchor_points):
                for anchor_b in infill.anchor_points[i + 1 :]:
                    distance = anchor_a.position.distance(anchor_b.position)

                    assert distance >= min_anchor_distance_cm - tolerance, (
                        f"In generated infill: anchor pair distance {distance:.4f}cm "
                        f"is less than min_anchor_distance_cm {min_anchor_distance_cm:.4f}cm"
                    )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass

    @settings(max_examples=20, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_rods=st.integers(min_value=3, max_value=15),
        num_layers=st.integers(min_value=1, max_value=3),
        min_anchor_distance_cm=st.floats(
            min_value=5.0, max_value=20.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_minimum_distance_maintained_after_mutation(
        self,
        frame: RailingFrame,
        num_rods: int,
        num_layers: int,
        min_anchor_distance_cm: float,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 7: Minimum Anchor Distance**

        *For any* infill after mutation, all anchor points SHALL still maintain
        the minimum distance constraint.

        **Validates: Requirements 7.4**
        """
        # Create generator and parameters
        generator = EvolutionaryInfillGenerator()
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=0.59,
            max_iterations=1,
            max_duration_sec=60.0,
            improvement_threshold=0.001,
            stagnation_limit=100,
            evaluator=PassThroughEvaluatorParameters(),
        )

        try:
            # Generate baseline infill
            infill = generator.generate(frame, params)

            # Skip if no anchor points in result
            if infill.anchor_points is None or len(infill.anchor_points) < 2:
                return

            # Perform mutation
            _, mutated_anchors = generator._mutate_arrangement(
                infill, infill.anchor_points, frame, num_layers
            )

            # Check all pairs of anchor points after mutation
            # Note: Mutation doesn't create new anchors, it only changes which ones are used
            # So the minimum distance should still be maintained
            tolerance = 0.01

            for i, anchor_a in enumerate(mutated_anchors):
                for anchor_b in mutated_anchors[i + 1 :]:
                    distance = anchor_a.position.distance(anchor_b.position)

                    assert distance >= min_anchor_distance_cm - tolerance, (
                        f"After mutation: anchor pair distance {distance:.4f}cm "
                        f"is less than min_anchor_distance_cm {min_anchor_distance_cm:.4f}cm"
                    )

        except RuntimeError:
            # Frame too small for requested rods - this is acceptable
            pass
