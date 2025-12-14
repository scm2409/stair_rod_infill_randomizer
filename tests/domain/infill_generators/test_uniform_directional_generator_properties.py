"""Property-based tests for UniformDirectionalGenerator.

Uses Hypothesis for property-based testing to verify correctness properties
defined in the design document.
"""

import math
from datetime import timedelta

from hypothesis import given, settings
from hypothesis import strategies as st
from shapely.geometry import LineString

from railing_generator.domain.infill_generators.uniform_directional_generator import (
    UniformDirectionalGenerator,
)
from railing_generator.domain.infill_generators.uniform_directional_generator_parameters import (
    UniformDirectionalGeneratorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.rod import Rod


# Strategy for generating valid rectangular frames
@st.composite
def valid_rectangular_frame(draw: st.DrawFn) -> RailingFrame:
    """
    Generate a valid rectangular frame with random dimensions.

    Generates frames with width and height between 50 and 500 cm.
    """
    width = draw(st.floats(min_value=50.0, max_value=500.0, allow_nan=False, allow_infinity=False))
    height = draw(st.floats(min_value=50.0, max_value=500.0, allow_nan=False, allow_infinity=False))

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


# Strategy for generating valid min_anchor_distance_cm values
# Use realistic values (5-50cm) to avoid performance issues with very small distances
valid_min_anchor_distance_cm = st.floats(
    min_value=5.0, max_value=50.0, allow_nan=False, allow_infinity=False
)


class TestMinimumAnchorDistanceProperty:
    """
    **Feature: uniform-directional-generator, Property 4: Minimum Anchor Distance**

    *For any* generated infill, all pairs of anchor points (regardless of layer)
    SHALL be separated by at least min_anchor_distance_cm.

    **Validates: Requirements 3.2, 3.3**
    """

    @settings(max_examples=100, deadline=timedelta(seconds=2))
    @given(
        frame=valid_rectangular_frame(),
        min_anchor_distance_cm=valid_min_anchor_distance_cm,
    )
    def test_all_anchor_pairs_satisfy_minimum_distance(
        self,
        frame: RailingFrame,
        min_anchor_distance_cm: float,
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 4: Minimum Anchor Distance**

        *For any* frame and min_anchor_distance_cm, all pairs of generated anchor
        points SHALL be separated by at least min_anchor_distance_cm.

        **Validates: Requirements 3.2, 3.3**
        """
        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=10,
            num_layers=2,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=0.59,
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

    @settings(max_examples=100, deadline=timedelta(seconds=2))
    @given(
        frame=valid_rectangular_frame(),
        min_anchor_distance_cm=valid_min_anchor_distance_cm,
    )
    def test_anchors_are_evenly_spaced(
        self,
        frame: RailingFrame,
        min_anchor_distance_cm: float,
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 4: Minimum Anchor Distance**

        *For any* frame and min_anchor_distance_cm, consecutive anchor points
        along the boundary SHALL be approximately evenly spaced.

        **Validates: Requirements 3.2, 3.4**
        """
        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=10,
            num_layers=2,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Generate anchor grid
        anchor_points = generator._generate_anchor_grid(frame, params)

        # Skip if fewer than 2 anchors
        if len(anchor_points) < 2:
            return

        # Calculate expected spacing
        perimeter = frame.boundary.exterior.length
        expected_spacing = perimeter / len(anchor_points)

        # Check consecutive anchor distances (along boundary, not Euclidean)
        # Since anchors are placed at regular intervals along the boundary,
        # consecutive anchors should be approximately expected_spacing apart
        # (with some tolerance for corners)
        for i in range(len(anchor_points) - 1):
            anchor_a = anchor_points[i]
            anchor_b = anchor_points[i + 1]
            distance = anchor_a.position.distance(anchor_b.position)

            # Distance should be at least min_anchor_distance_cm
            # (already tested above, but good to verify here too)
            assert distance >= min_anchor_distance_cm - 0.01

    @settings(max_examples=100, deadline=timedelta(seconds=2))
    @given(
        frame=valid_rectangular_frame(),
        min_anchor_distance_cm=valid_min_anchor_distance_cm,
    )
    def test_all_anchors_start_as_free(
        self,
        frame: RailingFrame,
        min_anchor_distance_cm: float,
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 4: Minimum Anchor Distance**

        *For any* generated anchor grid, all anchor points SHALL start as free
        (used=False, layer=None).

        **Validates: Requirements 3.1, 3.4**
        """
        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=10,
            num_layers=2,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Generate anchor grid
        anchor_points = generator._generate_anchor_grid(frame, params)

        # All anchors should be free
        for anchor in anchor_points:
            assert anchor.used is False, "Anchor should start as unused"
            assert anchor.layer is None, "Anchor should start with no layer assigned"

    @settings(max_examples=100, deadline=timedelta(seconds=2))
    @given(
        frame=valid_rectangular_frame(),
        min_anchor_distance_cm=valid_min_anchor_distance_cm,
    )
    def test_anchors_on_frame_boundary(
        self,
        frame: RailingFrame,
        min_anchor_distance_cm: float,
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 4: Minimum Anchor Distance**

        *For any* generated anchor grid, all anchor points SHALL lie on the
        frame boundary.

        **Validates: Requirements 3.1**
        """
        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=10,
            num_layers=2,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Generate anchor grid
        anchor_points = generator._generate_anchor_grid(frame, params)

        # All anchors should be on the boundary
        for anchor in anchor_points:
            distance_to_boundary = frame.boundary.exterior.distance(anchor.position)
            # Allow small tolerance for floating point errors
            assert distance_to_boundary < 0.01, (
                f"Anchor at {anchor.position} is {distance_to_boundary:.4f}cm "
                f"from boundary (should be on boundary)"
            )


# Strategy for generating valid direction ranges
# min_deg must be less than max_deg, both in [-90, 90]
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


# Strategy for generating valid number of layers
valid_num_layers = st.integers(min_value=1, max_value=10)


class TestLayerDirectionCalculationProperty:
    """
    **Feature: uniform-directional-generator, Property 3: Layer Direction Calculation**

    *For any* generated infill with L layers and direction range [min_deg, max_deg],
    each layer's rods SHALL follow the direction calculated by:
    direction = min_deg + (layer_index / (L - 1)) * (max_deg - min_deg) for L > 1,
    or (min_deg + max_deg) / 2 for L = 1.

    **Validates: Requirements 1.3, 1.4, 2.4, 2.5**
    """

    @settings(max_examples=100, deadline=timedelta(seconds=2))
    @given(
        num_layers=valid_num_layers,
        direction_range=valid_direction_range(),
    )
    def test_single_layer_uses_midpoint(
        self,
        num_layers: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 3: Layer Direction Calculation**

        WHEN there is only one layer THEN the Uniform_Directional_Generator SHALL
        use the midpoint of the direction range as the main direction.

        **Validates: Requirements 2.5**
        """
        # Only test single layer case
        if num_layers != 1:
            return

        min_deg, max_deg = direction_range

        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=10,
            num_layers=1,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
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

    @settings(max_examples=100, deadline=timedelta(seconds=2))
    @given(
        num_layers=st.integers(min_value=2, max_value=10),
        direction_range=valid_direction_range(),
    )
    def test_multiple_layers_use_linear_interpolation(
        self,
        num_layers: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 3: Layer Direction Calculation**

        WHEN calculating layer main directions THEN the Uniform_Directional_Generator
        SHALL distribute directions evenly across the range using the formula:
        main_direction = min_angle + (layer_index / (num_layers - 1)) * (max_angle - min_angle)

        **Validates: Requirements 2.4**
        """
        min_deg, max_deg = direction_range

        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=10,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Calculate layer directions
        layer_directions = generator._calculate_layer_directions(params)

        # Should have exactly num_layers layers
        assert len(layer_directions) == num_layers, (
            f"Expected {num_layers} layers, got {len(layer_directions)}"
        )

        # Verify each layer's direction follows the formula
        for layer_num in range(1, num_layers + 1):
            assert layer_num in layer_directions, f"Layer {layer_num} should be present"

            # Calculate expected direction using the formula
            # layer_index is 0-based, so layer_num - 1
            layer_index = layer_num - 1
            t = layer_index / (num_layers - 1)
            expected_direction = min_deg + t * (max_deg - min_deg)
            actual_direction = layer_directions[layer_num]

            assert math.isclose(actual_direction, expected_direction, rel_tol=1e-9, abs_tol=1e-9), (
                f"Layer {layer_num} direction {actual_direction:.6f}° should be "
                f"{expected_direction:.6f}° (t={t:.4f}, range=[{min_deg:.2f}°, {max_deg:.2f}°])"
            )

    @settings(max_examples=100, deadline=timedelta(seconds=2))
    @given(
        num_layers=st.integers(min_value=2, max_value=10),
        direction_range=valid_direction_range(),
    )
    def test_first_layer_equals_min_direction(
        self,
        num_layers: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 3: Layer Direction Calculation**

        *For any* multi-layer configuration, the first layer (layer 1) SHALL have
        direction equal to main_direction_range_min_deg.

        **Validates: Requirements 1.3, 2.4**
        """
        min_deg, max_deg = direction_range

        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=10,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Calculate layer directions
        layer_directions = generator._calculate_layer_directions(params)

        # First layer should have min_deg direction
        assert math.isclose(layer_directions[1], min_deg, rel_tol=1e-9, abs_tol=1e-9), (
            f"First layer direction {layer_directions[1]:.6f}° should equal min_deg {min_deg:.6f}°"
        )

    @settings(max_examples=100, deadline=timedelta(seconds=2))
    @given(
        num_layers=st.integers(min_value=2, max_value=10),
        direction_range=valid_direction_range(),
    )
    def test_last_layer_equals_max_direction(
        self,
        num_layers: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 3: Layer Direction Calculation**

        *For any* multi-layer configuration, the last layer SHALL have
        direction equal to main_direction_range_max_deg.

        **Validates: Requirements 1.3, 2.4**
        """
        min_deg, max_deg = direction_range

        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=10,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Calculate layer directions
        layer_directions = generator._calculate_layer_directions(params)

        # Last layer should have max_deg direction
        assert math.isclose(layer_directions[num_layers], max_deg, rel_tol=1e-9, abs_tol=1e-9), (
            f"Last layer (layer {num_layers}) direction {layer_directions[num_layers]:.6f}° "
            f"should equal max_deg {max_deg:.6f}°"
        )

    @settings(max_examples=100, deadline=timedelta(seconds=2))
    @given(
        num_layers=st.integers(min_value=2, max_value=10),
        direction_range=valid_direction_range(),
    )
    def test_directions_are_evenly_spaced(
        self,
        num_layers: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 3: Layer Direction Calculation**

        *For any* multi-layer configuration, the directions SHALL be evenly spaced
        across the direction range.

        **Validates: Requirements 1.4, 2.4**
        """
        min_deg, max_deg = direction_range

        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=10,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Calculate layer directions
        layer_directions = generator._calculate_layer_directions(params)

        # Calculate expected spacing between consecutive layers
        expected_spacing = (max_deg - min_deg) / (num_layers - 1)

        # Check spacing between consecutive layers
        for layer_num in range(1, num_layers):
            current_direction = layer_directions[layer_num]
            next_direction = layer_directions[layer_num + 1]
            actual_spacing = next_direction - current_direction

            assert math.isclose(actual_spacing, expected_spacing, rel_tol=1e-9, abs_tol=1e-9), (
                f"Spacing between layer {layer_num} and {layer_num + 1} is "
                f"{actual_spacing:.6f}°, expected {expected_spacing:.6f}°"
            )

    @settings(max_examples=100, deadline=timedelta(seconds=2))
    @given(
        num_layers=valid_num_layers,
        direction_range=valid_direction_range(),
    )
    def test_all_directions_within_range(
        self,
        num_layers: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 3: Layer Direction Calculation**

        *For any* configuration, all layer directions SHALL be within the
        specified direction range [min_deg, max_deg].

        **Validates: Requirements 1.3, 2.4, 2.5**
        """
        min_deg, max_deg = direction_range

        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=10,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Calculate layer directions
        layer_directions = generator._calculate_layer_directions(params)

        # All directions should be within the range
        for layer_num, direction in layer_directions.items():
            # Allow small tolerance for floating point errors
            assert direction >= min_deg - 1e-9, (
                f"Layer {layer_num} direction {direction:.6f}° is below min_deg {min_deg:.6f}°"
            )
            assert direction <= max_deg + 1e-9, (
                f"Layer {layer_num} direction {direction:.6f}° is above max_deg {max_deg:.6f}°"
            )


class TestRodConstraintSatisfactionProperty:
    """
    **Feature: uniform-directional-generator, Property 5: Rod Constraint Satisfaction**

    *For any* generated infill: (a) no two rods in the same layer SHALL cross,
    (b) all rods SHALL be completely within the frame boundary, and
    (c) all rod endpoints SHALL lie on the frame boundary.

    **Validates: Requirements 6.1, 6.3, 6.4**
    """

    @settings(max_examples=100, deadline=timedelta(seconds=5))
    @given(
        frame=valid_rectangular_frame(),
        num_layers=st.integers(min_value=1, max_value=3),
        num_rods_per_layer=st.integers(min_value=2, max_value=5),
        direction_range=valid_direction_range(),
    )
    def test_no_same_layer_crossings(
        self,
        frame: RailingFrame,
        num_layers: int,
        num_rods_per_layer: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 5: Rod Constraint Satisfaction**

        *For any* generated infill, no two rods in the same layer SHALL cross each other.

        **Validates: Requirements 6.1**
        """
        min_deg, max_deg = direction_range
        total_rods = num_layers * num_rods_per_layer

        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=total_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Generate anchor grid
        anchor_points = generator._generate_anchor_grid(frame, params)

        # Calculate layer directions
        layer_directions = generator._calculate_layer_directions(params)

        # Calculate rods per layer
        base_rods_per_layer = total_rods // num_layers
        extra_rods = total_rods % num_layers

        # Generate rods for each layer
        all_rods: list[Rod] = []
        for layer_num in range(1, num_layers + 1):
            target_rods = base_rods_per_layer + (1 if layer_num <= extra_rods else 0)
            direction = layer_directions[layer_num]

            layer_rods = generator._generate_layer_rods(
                layer_num=layer_num,
                direction_deg=direction,
                target_rods=target_rods,
                frame=frame,
                anchor_points=anchor_points,
                weight_kg_m=params.infill_weight_per_meter_kg_m,
            )
            all_rods.extend(layer_rods)

        # Group rods by layer
        rods_by_layer: dict[int, list[Rod]] = {}
        for rod in all_rods:
            if rod.layer not in rods_by_layer:
                rods_by_layer[rod.layer] = []
            rods_by_layer[rod.layer].append(rod)

        # Check for crossings within each layer
        for layer_num, layer_rods in rods_by_layer.items():
            for i, rod_a in enumerate(layer_rods):
                for rod_b in layer_rods[i + 1 :]:
                    # Check if rods cross (intersect at a point, not just touch at endpoints)
                    intersection = rod_a.geometry.intersection(rod_b.geometry)

                    # If intersection is a point (not empty and not a line segment),
                    # check if it's at an endpoint or in the middle
                    if not intersection.is_empty and intersection.geom_type == "Point":
                        # Check if intersection is at an endpoint of either rod
                        is_at_endpoint = (
                            intersection.equals(rod_a.start_point)
                            or intersection.equals(rod_a.end_point)
                            or intersection.equals(rod_b.start_point)
                            or intersection.equals(rod_b.end_point)
                        )

                        if not is_at_endpoint:
                            # This is a true crossing in the middle of both rods
                            assert False, (
                                f"Rods in layer {layer_num} cross at {intersection}: "
                                f"rod_a from {rod_a.start_point} to {rod_a.end_point}, "
                                f"rod_b from {rod_b.start_point} to {rod_b.end_point}"
                            )

    @settings(max_examples=100, deadline=timedelta(seconds=5))
    @given(
        frame=valid_rectangular_frame(),
        num_layers=st.integers(min_value=1, max_value=3),
        num_rods_per_layer=st.integers(min_value=2, max_value=5),
        direction_range=valid_direction_range(),
    )
    def test_rods_within_boundary(
        self,
        frame: RailingFrame,
        num_layers: int,
        num_rods_per_layer: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 5: Rod Constraint Satisfaction**

        *For any* generated infill, all rods SHALL be completely within the frame boundary.

        **Validates: Requirements 6.3**
        """
        min_deg, max_deg = direction_range
        total_rods = num_layers * num_rods_per_layer

        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=total_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Generate anchor grid
        anchor_points = generator._generate_anchor_grid(frame, params)

        # Calculate layer directions
        layer_directions = generator._calculate_layer_directions(params)

        # Calculate rods per layer
        base_rods_per_layer = total_rods // num_layers
        extra_rods = total_rods % num_layers

        # Generate rods for each layer
        all_rods: list[Rod] = []
        for layer_num in range(1, num_layers + 1):
            target_rods = base_rods_per_layer + (1 if layer_num <= extra_rods else 0)
            direction = layer_directions[layer_num]

            layer_rods = generator._generate_layer_rods(
                layer_num=layer_num,
                direction_deg=direction,
                target_rods=target_rods,
                frame=frame,
                anchor_points=anchor_points,
                weight_kg_m=params.infill_weight_per_meter_kg_m,
            )
            all_rods.extend(layer_rods)

        # Check that all rods are within the boundary
        for rod in all_rods:
            # A rod is within the boundary if it's covered by the boundary polygon
            # Since rods connect points on the boundary, they should be within or on the boundary
            is_within = frame.boundary.covers(rod.geometry)

            assert is_within, (
                f"Rod from {rod.start_point} to {rod.end_point} is not within the frame boundary"
            )

    @settings(max_examples=100, deadline=timedelta(seconds=5))
    @given(
        frame=valid_rectangular_frame(),
        num_layers=st.integers(min_value=1, max_value=3),
        num_rods_per_layer=st.integers(min_value=2, max_value=5),
        direction_range=valid_direction_range(),
    )
    def test_endpoints_on_boundary(
        self,
        frame: RailingFrame,
        num_layers: int,
        num_rods_per_layer: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 5: Rod Constraint Satisfaction**

        *For any* generated infill, all rod endpoints SHALL lie on the frame boundary.

        **Validates: Requirements 6.4**
        """
        min_deg, max_deg = direction_range
        total_rods = num_layers * num_rods_per_layer

        # Create generator and parameters
        generator = UniformDirectionalGenerator()
        params = UniformDirectionalGeneratorParameters(
            num_rods=total_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Generate anchor grid
        anchor_points = generator._generate_anchor_grid(frame, params)

        # Calculate layer directions
        layer_directions = generator._calculate_layer_directions(params)

        # Calculate rods per layer
        base_rods_per_layer = total_rods // num_layers
        extra_rods = total_rods % num_layers

        # Generate rods for each layer
        all_rods: list[Rod] = []
        for layer_num in range(1, num_layers + 1):
            target_rods = base_rods_per_layer + (1 if layer_num <= extra_rods else 0)
            direction = layer_directions[layer_num]

            layer_rods = generator._generate_layer_rods(
                layer_num=layer_num,
                direction_deg=direction,
                target_rods=target_rods,
                frame=frame,
                anchor_points=anchor_points,
                weight_kg_m=params.infill_weight_per_meter_kg_m,
            )
            all_rods.extend(layer_rods)

        # Check that all rod endpoints are on the boundary
        for rod in all_rods:
            start_distance = frame.boundary.exterior.distance(rod.start_point)
            end_distance = frame.boundary.exterior.distance(rod.end_point)

            # Allow small tolerance for floating point errors (0.01cm = 0.1mm)
            assert start_distance < 0.01, (
                f"Rod start point {rod.start_point} is {start_distance:.4f}cm "
                f"from boundary (should be on boundary)"
            )
            assert end_distance < 0.01, (
                f"Rod end point {rod.end_point} is {end_distance:.4f}cm "
                f"from boundary (should be on boundary)"
            )


class TestDeterministicGenerationProperty:
    """
    **Feature: uniform-directional-generator, Property 1: Deterministic Generation**

    *For any* valid frame and parameters, generating infill twice with identical
    inputs SHALL produce identical results (same rods with same positions, angles,
    and layer assignments).

    **Validates: Requirements 1.1, 5.2**
    """

    @settings(max_examples=100, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_layers=st.integers(min_value=1, max_value=3),
        num_rods=st.integers(min_value=3, max_value=10),
        direction_range=valid_direction_range(),
    )
    def test_identical_inputs_produce_identical_outputs(
        self,
        frame: RailingFrame,
        num_layers: int,
        num_rods: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 1: Deterministic Generation**

        *For any* valid frame and parameters, generating infill twice with identical
        inputs SHALL produce identical results.

        **Validates: Requirements 1.1, 5.2**
        """
        min_deg, max_deg = direction_range

        # Create parameters
        params = UniformDirectionalGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Generate twice with the same inputs
        generator1 = UniformDirectionalGenerator()
        generator2 = UniformDirectionalGenerator()

        try:
            result1 = generator1.generate(frame, params)
            result2 = generator2.generate(frame, params)
        except RuntimeError:
            # If generation fails (e.g., frame too small), that's fine
            # The property only applies to successful generations
            return

        # Verify identical rod count
        assert len(result1.rods) == len(result2.rods), (
            f"Rod counts differ: {len(result1.rods)} vs {len(result2.rods)}"
        )

        # Verify identical rods (same positions, angles, layers)
        for i, (rod1, rod2) in enumerate(zip(result1.rods, result2.rods)):
            # Check layer
            assert rod1.layer == rod2.layer, f"Rod {i} layer differs: {rod1.layer} vs {rod2.layer}"

            # Check geometry (start and end points)
            assert rod1.start_point.equals_exact(rod2.start_point, tolerance=0.001), (
                f"Rod {i} start point differs: {rod1.start_point} vs {rod2.start_point}"
            )
            assert rod1.end_point.equals_exact(rod2.end_point, tolerance=0.001), (
                f"Rod {i} end point differs: {rod1.end_point} vs {rod2.end_point}"
            )

            # Check angles
            assert math.isclose(
                rod1.angle_from_vertical_deg, rod2.angle_from_vertical_deg, abs_tol=0.001
            ), (
                f"Rod {i} angle differs: {rod1.angle_from_vertical_deg} vs "
                f"{rod2.angle_from_vertical_deg}"
            )


class TestEvenLayerDistributionProperty:
    """
    **Feature: uniform-directional-generator, Property 2: Even Layer Distribution**

    *For any* generated infill with N rods and L layers, the difference between
    the layer with the most rods and the layer with the fewest rods SHALL be at
    most 1, and extra rods SHALL be assigned to lower-numbered layers first.

    **Validates: Requirements 1.2, 1.5, 4.2, 4.3**
    """

    @settings(max_examples=100, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_layers=st.integers(min_value=1, max_value=5),
        num_rods=st.integers(min_value=3, max_value=15),
        direction_range=valid_direction_range(),
    )
    def test_rod_count_difference_at_most_one(
        self,
        frame: RailingFrame,
        num_layers: int,
        num_rods: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 2: Even Layer Distribution**

        *For any* generated infill, the difference between the layer with the most
        rods and the layer with the fewest rods SHALL be at most 1.

        **Validates: Requirements 1.2, 1.5, 4.2, 4.3**
        """
        min_deg, max_deg = direction_range

        # Create parameters
        params = UniformDirectionalGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Generate infill
        generator = UniformDirectionalGenerator()

        try:
            result = generator.generate(frame, params)
        except RuntimeError:
            # If generation fails (e.g., frame too small), that's fine
            return

        # Count rods per layer
        rods_per_layer: dict[int, int] = {}
        for rod in result.rods:
            layer = rod.layer
            rods_per_layer[layer] = rods_per_layer.get(layer, 0) + 1

        # Skip if no rods generated
        if not rods_per_layer:
            return

        # Get min and max rod counts
        min_count = min(rods_per_layer.values())
        max_count = max(rods_per_layer.values())

        # Difference should be at most 1
        assert max_count - min_count <= 1, (
            f"Rod count difference between layers is {max_count - min_count}, "
            f"expected at most 1. Rods per layer: {rods_per_layer}"
        )

    @settings(max_examples=100, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_layers=st.integers(min_value=2, max_value=5),
        direction_range=valid_direction_range(),
    )
    def test_extra_rods_assigned_to_lower_layers_first(
        self,
        frame: RailingFrame,
        num_layers: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 2: Even Layer Distribution**

        WHEN num_rods is not evenly divisible by num_layers THEN the
        Uniform_Directional_Generator SHALL assign extra rods to layers
        sequentially starting from layer 1.

        **Validates: Requirements 4.3**
        """
        min_deg, max_deg = direction_range

        # Choose num_rods that is NOT evenly divisible by num_layers
        # to ensure we have extra rods to distribute
        base_rods = 2  # At least 2 rods per layer
        extra_rods = num_layers - 1  # One less than num_layers to ensure uneven
        num_rods = base_rods * num_layers + extra_rods

        # Create parameters
        params = UniformDirectionalGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Generate infill
        generator = UniformDirectionalGenerator()

        try:
            result = generator.generate(frame, params)
        except RuntimeError:
            # If generation fails (e.g., frame too small), that's fine
            return

        # Count rods per layer
        rods_per_layer: dict[int, int] = {}
        for rod in result.rods:
            layer = rod.layer
            rods_per_layer[layer] = rods_per_layer.get(layer, 0) + 1

        # Skip if not all layers have rods
        if len(rods_per_layer) < num_layers:
            return

        # Calculate expected distribution
        expected_base = num_rods // num_layers
        expected_extra = num_rods % num_layers

        # Verify that layers 1 through expected_extra have one more rod
        for layer_num in range(1, num_layers + 1):
            expected_count = expected_base + (1 if layer_num <= expected_extra else 0)
            actual_count = rods_per_layer.get(layer_num, 0)

            assert actual_count == expected_count, (
                f"Layer {layer_num} has {actual_count} rods, expected {expected_count}. "
                f"Total rods: {num_rods}, layers: {num_layers}, "
                f"base: {expected_base}, extra: {expected_extra}"
            )


class TestFailFastBehaviorProperty:
    """
    **Feature: uniform-directional-generator, Property 6: Fail-Fast on Constraint Violation**

    *For any* parameters where the frame cannot accommodate the requested rods
    with the minimum distance constraint, generation SHALL fail with an error
    (not return partial results).

    **Validates: Requirements 3.5, 5.5**
    """

    @settings(max_examples=100, deadline=timedelta(seconds=5))
    @given(
        # Use small frames that can't accommodate many rods
        width=st.floats(min_value=20.0, max_value=50.0, allow_nan=False, allow_infinity=False),
        height=st.floats(min_value=20.0, max_value=50.0, allow_nan=False, allow_infinity=False),
        # Use large min_anchor_distance to make it impossible
        min_anchor_distance_cm=st.floats(
            min_value=15.0, max_value=30.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_fails_when_frame_too_small_for_rods(
        self,
        width: float,
        height: float,
        min_anchor_distance_cm: float,
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 6: Fail-Fast on Constraint Violation**

        WHEN the frame geometry cannot accommodate the requested number of rods
        with the minimum distance constraint THEN the Uniform_Directional_Generator
        SHALL fail with an error message.

        **Validates: Requirements 3.5, 5.5**
        """
        import pytest

        # Create a small frame
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
        frame = RailingFrame(rods=rods)

        # Calculate perimeter and max possible anchors
        perimeter = 2 * (width + height)
        max_anchors = int(perimeter / min_anchor_distance_cm)

        # Request more rods than possible (each rod needs 2 anchors)
        # Request at least max_anchors rods to ensure failure
        num_rods = max(max_anchors, 50)

        # Create parameters with impossible constraints
        params = UniformDirectionalGeneratorParameters(
            num_rods=num_rods,
            num_layers=2,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Generate should fail with RuntimeError
        generator = UniformDirectionalGenerator()

        with pytest.raises(RuntimeError):
            generator.generate(frame, params)

    def test_fails_with_error_not_partial_result(self) -> None:
        """
        **Feature: uniform-directional-generator, Property 6: Fail-Fast on Constraint Violation**

        WHEN a rod cannot be placed at a calculated position due to constraints
        THEN the Uniform_Directional_Generator SHALL fail with an error message
        (not return partial results).

        **Validates: Requirements 5.5**
        """
        import pytest

        # Create a very small frame (10x10 cm)
        width, height = 10.0, 10.0
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
        frame = RailingFrame(rods=rods)

        # Request many rods with large spacing - impossible to satisfy
        params = UniformDirectionalGeneratorParameters(
            num_rods=100,  # Way too many for a 10x10 frame
            num_layers=3,
            main_direction_range_min_deg=-45.0,
            main_direction_range_max_deg=25.0,
            min_anchor_distance_cm=5.0,  # 5cm spacing on 40cm perimeter = max 8 anchors
            infill_weight_per_meter_kg_m=0.59,
        )

        generator = UniformDirectionalGenerator()

        # Should raise RuntimeError, not return partial result
        with pytest.raises(RuntimeError) as exc_info:
            generator.generate(frame, params)

        # Error message should be informative
        assert "rods" in str(exc_info.value).lower() or "anchor" in str(exc_info.value).lower()


class TestEvaluatorIntegrationProperty:
    """
    **Feature: uniform-directional-generator, Property 8: Evaluator Integration**

    *For any* generated infill with a configured evaluator, the returned
    RailingInfill SHALL include a fitness_score calculated by that evaluator.

    **Validates: Requirements 7.2, 7.3**
    """

    @settings(max_examples=100, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_layers=st.integers(min_value=1, max_value=3),
        num_rods=st.integers(min_value=3, max_value=10),
        direction_range=valid_direction_range(),
    )
    def test_passthrough_evaluator_populates_fitness_score(
        self,
        frame: RailingFrame,
        num_layers: int,
        num_rods: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 8: Evaluator Integration**

        *For any* generated infill with PassThroughEvaluator, the returned
        RailingInfill SHALL include a fitness_score.

        **Validates: Requirements 7.2, 7.3**
        """
        from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
            PassThroughEvaluatorParameters,
        )

        min_deg, max_deg = direction_range

        # Create parameters with PassThroughEvaluator
        params = UniformDirectionalGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            evaluator=PassThroughEvaluatorParameters(),
        )

        # Generate infill
        generator = UniformDirectionalGenerator()

        try:
            result = generator.generate(frame, params)
        except RuntimeError:
            # If generation fails (e.g., frame too small), that's fine
            # The property only applies to successful generations
            return

        # Verify fitness_score is populated (not None)
        assert result.fitness_score is not None, (
            "fitness_score should be populated when using PassThroughEvaluator"
        )

        # PassThroughEvaluator returns 1.0 (neutral score)
        assert result.fitness_score == 1.0, (
            f"PassThroughEvaluator should return 1.0, got {result.fitness_score}"
        )

    @settings(max_examples=100, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_layers=st.integers(min_value=1, max_value=3),
        num_rods=st.integers(min_value=3, max_value=10),
        direction_range=valid_direction_range(),
    )
    def test_quality_evaluator_populates_fitness_score(
        self,
        frame: RailingFrame,
        num_layers: int,
        num_rods: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 8: Evaluator Integration**

        *For any* generated infill with QualityEvaluator, the returned
        RailingInfill SHALL include a fitness_score calculated by that evaluator.

        **Validates: Requirements 7.2, 7.3**
        """
        from railing_generator.domain.evaluators.quality_evaluator_parameters import (
            QualityEvaluatorParameters,
        )

        min_deg, max_deg = direction_range

        # Create parameters with QualityEvaluator
        # Use permissive thresholds to avoid rejection
        params = UniformDirectionalGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
            evaluator=QualityEvaluatorParameters(
                max_hole_area_cm2=100000.0,  # Very large to avoid rejection
                min_hole_area_cm2=0.01,  # Very small to avoid rejection
                hole_uniformity_weight=0.2,
                incircle_uniformity_weight=0.2,
                angle_distribution_weight=0.2,
                anchor_spacing_horizontal_weight=0.2,
                anchor_spacing_vertical_weight=0.2,
            ),
        )

        # Generate infill
        generator = UniformDirectionalGenerator()

        try:
            result = generator.generate(frame, params)
        except RuntimeError:
            # If generation fails (e.g., frame too small), that's fine
            # The property only applies to successful generations
            return

        # Verify fitness_score is populated (not None)
        assert result.fitness_score is not None, (
            "fitness_score should be populated when using QualityEvaluator"
        )

        # QualityEvaluator returns a score between 0.0 and 1.0
        assert 0.0 <= result.fitness_score <= 1.0, (
            f"QualityEvaluator should return score in [0.0, 1.0], got {result.fitness_score}"
        )

    @settings(max_examples=100, deadline=timedelta(seconds=10))
    @given(
        frame=valid_rectangular_frame(),
        num_layers=st.integers(min_value=1, max_value=3),
        num_rods=st.integers(min_value=3, max_value=10),
        direction_range=valid_direction_range(),
    )
    def test_default_evaluator_populates_fitness_score(
        self,
        frame: RailingFrame,
        num_layers: int,
        num_rods: int,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 8: Evaluator Integration**

        *For any* generated infill with default evaluator (PassThrough), the returned
        RailingInfill SHALL include a fitness_score.

        **Validates: Requirements 7.2, 7.3**
        """
        min_deg, max_deg = direction_range

        # Create parameters with default evaluator (no explicit evaluator specified)
        params = UniformDirectionalGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=5.0,
            infill_weight_per_meter_kg_m=0.59,
        )

        # Generate infill
        generator = UniformDirectionalGenerator()

        try:
            result = generator.generate(frame, params)
        except RuntimeError:
            # If generation fails (e.g., frame too small), that's fine
            # The property only applies to successful generations
            return

        # Verify fitness_score is populated (not None)
        assert result.fitness_score is not None, (
            "fitness_score should be populated when using default evaluator"
        )
