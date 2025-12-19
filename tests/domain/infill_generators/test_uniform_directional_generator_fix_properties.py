"""Property-based tests for UniformDirectionalGenerator fix.

Tests the polygon extent calculation fix that ensures even rod distribution
across the entire frame area, including non-rectangular shapes like parallelograms.

Uses Hypothesis for property-based testing to verify correctness properties
defined in the design document.
"""

import math
from datetime import timedelta

from hypothesis import given, settings
from hypothesis import strategies as st
from shapely.geometry import LineString, Polygon

from railing_generator.domain.infill_generators.uniform_directional_generator import (
    UniformDirectionalGenerator,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.rod import Rod


# Strategy for generating valid convex polygons (rectangles and parallelograms)
@st.composite
def valid_convex_polygon(draw: st.DrawFn) -> Polygon:
    """
    Generate a valid convex polygon (rectangle or parallelogram).

    Generates polygons with width and height between 50 and 500 cm.
    For parallelograms, adds a skew offset to create non-rectangular shapes.
    """
    width = draw(st.floats(min_value=50.0, max_value=500.0, allow_nan=False, allow_infinity=False))
    height = draw(st.floats(min_value=50.0, max_value=500.0, allow_nan=False, allow_infinity=False))

    # Optionally add skew to create a parallelogram
    # Skew is limited to avoid degenerate shapes
    max_skew = min(width * 0.5, height * 0.5)
    skew = draw(
        st.floats(min_value=-max_skew, max_value=max_skew, allow_nan=False, allow_infinity=False)
    )

    # Create polygon vertices (counterclockwise)
    # For a parallelogram, the top edge is shifted by 'skew'
    vertices = [
        (0, 0),  # bottom-left
        (width, 0),  # bottom-right
        (width + skew, height),  # top-right (shifted by skew)
        (skew, height),  # top-left (shifted by skew)
        (0, 0),  # close the polygon
    ]

    return Polygon(vertices)


# Strategy for generating direction angles
valid_direction_angle = st.floats(
    min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False
)


class TestPolygonExtentCalculationProperty:
    """
    **Feature: uniform-directional-generator-fix, Property 1: Polygon Extent Calculation**

    *For any* convex polygon and any direction angle, the calculated polygon extent
    (min_proj, max_proj) SHALL equal the minimum and maximum values when projecting
    all polygon vertices onto the perpendicular direction.

    **Validates: Requirements 1.1, 1.2**
    """

    @settings(max_examples=20, deadline=timedelta(seconds=2))
    @given(
        polygon=valid_convex_polygon(),
        direction_deg=valid_direction_angle,
    )
    def test_extent_matches_vertex_projections(
        self,
        polygon: Polygon,
        direction_deg: float,
    ) -> None:
        """
        **Feature: uniform-directional-generator-fix, Property 1: Polygon Extent Calculation**

        *For any* convex polygon and direction angle, the calculated extent SHALL
        match the min/max of all vertex projections onto the perpendicular direction.

        **Validates: Requirements 1.1, 1.2**
        """
        generator = UniformDirectionalGenerator()

        # Calculate perpendicular direction (same as in _generate_line_pattern)
        angle_rad = math.radians(direction_deg)
        line_dx = math.sin(angle_rad)
        line_dy = math.cos(angle_rad)
        perp_dx = -line_dy
        perp_dy = line_dx
        perpendicular_direction = (perp_dx, perp_dy)

        # Call the method under test
        min_proj, max_proj = generator._calculate_polygon_extent(polygon, perpendicular_direction)

        # Calculate expected values by projecting all vertices
        coords = list(polygon.exterior.coords)[:-1]  # Exclude closing vertex
        expected_projections = [vx * perp_dx + vy * perp_dy for vx, vy in coords]
        expected_min = min(expected_projections)
        expected_max = max(expected_projections)

        # Verify the calculated extent matches expected
        assert math.isclose(min_proj, expected_min, rel_tol=1e-9, abs_tol=1e-9), (
            f"min_proj {min_proj:.6f} should equal expected {expected_min:.6f}"
        )
        assert math.isclose(max_proj, expected_max, rel_tol=1e-9, abs_tol=1e-9), (
            f"max_proj {max_proj:.6f} should equal expected {expected_max:.6f}"
        )

    @settings(max_examples=20, deadline=timedelta(seconds=2))
    @given(
        polygon=valid_convex_polygon(),
        direction_deg=valid_direction_angle,
    )
    def test_extent_range_is_non_negative(
        self,
        polygon: Polygon,
        direction_deg: float,
    ) -> None:
        """
        **Feature: uniform-directional-generator-fix, Property 1: Polygon Extent Calculation**

        *For any* convex polygon and direction angle, the extent range (max - min)
        SHALL be non-negative.

        **Validates: Requirements 1.1, 1.2**
        """
        generator = UniformDirectionalGenerator()

        # Calculate perpendicular direction
        angle_rad = math.radians(direction_deg)
        perp_dx = -math.cos(angle_rad)
        perp_dy = math.sin(angle_rad)
        perpendicular_direction = (perp_dx, perp_dy)

        # Call the method under test
        min_proj, max_proj = generator._calculate_polygon_extent(polygon, perpendicular_direction)

        # Verify range is non-negative
        extent_range = max_proj - min_proj
        assert extent_range >= 0, (
            f"Extent range {extent_range:.6f} should be non-negative "
            f"(min={min_proj:.6f}, max={max_proj:.6f})"
        )

    @settings(max_examples=20, deadline=timedelta(seconds=2))
    @given(
        polygon=valid_convex_polygon(),
        direction_deg=valid_direction_angle,
    )
    def test_extent_covers_all_vertices(
        self,
        polygon: Polygon,
        direction_deg: float,
    ) -> None:
        """
        **Feature: uniform-directional-generator-fix, Property 1: Polygon Extent Calculation**

        *For any* convex polygon and direction angle, all vertex projections SHALL
        fall within the calculated extent [min_proj, max_proj].

        **Validates: Requirements 1.1, 1.2**
        """
        generator = UniformDirectionalGenerator()

        # Calculate perpendicular direction
        angle_rad = math.radians(direction_deg)
        perp_dx = -math.cos(angle_rad)
        perp_dy = math.sin(angle_rad)
        perpendicular_direction = (perp_dx, perp_dy)

        # Call the method under test
        min_proj, max_proj = generator._calculate_polygon_extent(polygon, perpendicular_direction)

        # Verify all vertices fall within the extent
        coords = list(polygon.exterior.coords)[:-1]
        for vx, vy in coords:
            projection = vx * perp_dx + vy * perp_dy
            # Allow small tolerance for floating point errors
            assert projection >= min_proj - 1e-9, (
                f"Vertex ({vx:.2f}, {vy:.2f}) projection {projection:.6f} "
                f"is below min_proj {min_proj:.6f}"
            )
            assert projection <= max_proj + 1e-9, (
                f"Vertex ({vx:.2f}, {vy:.2f}) projection {projection:.6f} "
                f"is above max_proj {max_proj:.6f}"
            )

    @settings(max_examples=20, deadline=timedelta(seconds=2))
    @given(
        polygon=valid_convex_polygon(),
    )
    def test_vertical_direction_extent(
        self,
        polygon: Polygon,
    ) -> None:
        """
        **Feature: uniform-directional-generator-fix, Property 1: Polygon Extent Calculation**

        *For any* convex polygon with direction 0° (vertical), the perpendicular
        direction is horizontal, so the extent should match the polygon's x-range.

        **Validates: Requirements 1.1, 1.2**
        """
        generator = UniformDirectionalGenerator()

        # For 0° direction (vertical lines), perpendicular is horizontal (-1, 0)
        perpendicular_direction = (-1.0, 0.0)

        # Call the method under test
        min_proj, max_proj = generator._calculate_polygon_extent(polygon, perpendicular_direction)

        # For horizontal perpendicular, projections are -x values
        # So min_proj corresponds to max x, and max_proj corresponds to min x
        coords = list(polygon.exterior.coords)[:-1]
        x_values = [vx for vx, vy in coords]
        expected_min = -max(x_values)  # -max_x
        expected_max = -min(x_values)  # -min_x

        assert math.isclose(min_proj, expected_min, rel_tol=1e-9, abs_tol=1e-9), (
            f"For vertical direction, min_proj {min_proj:.6f} should equal {expected_min:.6f}"
        )
        assert math.isclose(max_proj, expected_max, rel_tol=1e-9, abs_tol=1e-9), (
            f"For vertical direction, max_proj {max_proj:.6f} should equal {expected_max:.6f}"
        )


# Strategy for generating valid frames (rectangles and parallelograms)
@st.composite
def valid_frame(draw: st.DrawFn) -> RailingFrame:
    """
    Generate a valid frame (rectangle or parallelogram).

    Generates frames with width and height between 50 and 500 cm.
    For parallelograms, adds a skew offset to create non-rectangular shapes.
    """
    width = draw(st.floats(min_value=50.0, max_value=500.0, allow_nan=False, allow_infinity=False))
    height = draw(st.floats(min_value=50.0, max_value=500.0, allow_nan=False, allow_infinity=False))

    # Optionally add skew to create a parallelogram
    # Skew is limited to avoid degenerate shapes
    max_skew = min(width * 0.5, height * 0.5)
    skew = draw(
        st.floats(min_value=-max_skew, max_value=max_skew, allow_nan=False, allow_infinity=False)
    )

    # Create frame rods for a parallelogram
    # Bottom: (0, 0) -> (width, 0)
    # Right: (width, 0) -> (width + skew, height)
    # Top: (width + skew, height) -> (skew, height)
    # Left: (skew, height) -> (0, 0)
    rods = [
        Rod(
            geometry=LineString([(0, 0), (width, 0)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(width, 0), (width + skew, height)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(width + skew, height), (skew, height)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(skew, height), (0, 0)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
    ]

    return RailingFrame(rods=rods)


# Strategy for generating number of lines (2-20 for meaningful distribution tests)
valid_num_lines = st.integers(min_value=2, max_value=20)


class TestEvenDistributionProperty:
    """
    **Feature: uniform-directional-generator-fix, Property 2: Even Distribution Across Polygon Extent**

    *For any* generated line pattern with N lines, the lines SHALL be evenly spaced
    across the actual polygon extent, with the first line at or near the minimum
    extent and the last line at or near the maximum extent.

    **Validates: Requirements 1.3, 1.4, 1.5, 2.1, 2.3**
    """

    @settings(max_examples=20, deadline=timedelta(seconds=2))
    @given(
        frame=valid_frame(),
        direction_deg=valid_direction_angle,
        num_lines=valid_num_lines,
    )
    def test_lines_evenly_spaced_across_polygon_extent(
        self,
        frame: RailingFrame,
        direction_deg: float,
        num_lines: int,
    ) -> None:
        """
        **Feature: uniform-directional-generator-fix, Property 2: Even Distribution Across Polygon Extent**

        *For any* frame, direction, and number of lines, the generated lines SHALL
        be evenly spaced across the valid line range (where lines produce two-point
        intersections).

        **Validates: Requirements 1.3, 1.4, 1.5, 2.1, 2.3**
        """
        generator = UniformDirectionalGenerator()

        # Generate line pattern
        lines = generator._generate_line_pattern(frame, direction_deg, num_lines)

        # Verify we got the expected number of lines
        assert len(lines) == num_lines, f"Expected {num_lines} lines, got {len(lines)}"

        # Calculate line and perpendicular directions
        angle_rad = math.radians(direction_deg)
        line_dx = math.sin(angle_rad)
        line_dy = math.cos(angle_rad)
        perp_dx = -math.cos(angle_rad)
        perp_dy = math.sin(angle_rad)

        # Get the valid line range (where lines produce two-point intersections)
        line_direction = (line_dx, line_dy)
        perpendicular_direction = (perp_dx, perp_dy)
        min_proj, max_proj = generator._calculate_valid_line_range(
            frame.boundary, line_direction, perpendicular_direction
        )
        expected_range = max_proj - min_proj

        # Calculate the projection of each line's center point onto the perpendicular direction
        line_projections: list[float] = []
        for line in lines:
            # Get the center point of the line
            center = line.centroid
            projection = center.x * perp_dx + center.y * perp_dy
            line_projections.append(projection)

        # Sort projections to check spacing
        line_projections.sort()

        # Calculate expected spacing
        expected_spacing = expected_range / (num_lines - 1)

        # Verify lines are evenly spaced
        for i in range(1, len(line_projections)):
            actual_spacing = line_projections[i] - line_projections[i - 1]
            # Allow 1% tolerance for floating point errors
            tolerance = max(expected_spacing * 0.01, 0.01)
            assert math.isclose(actual_spacing, expected_spacing, abs_tol=tolerance), (
                f"Line spacing {actual_spacing:.4f} differs from expected {expected_spacing:.4f} "
                f"(tolerance={tolerance:.4f})"
            )

    @settings(max_examples=20, deadline=timedelta(seconds=2))
    @given(
        frame=valid_frame(),
        direction_deg=valid_direction_angle,
        num_lines=valid_num_lines,
    )
    def test_first_line_at_polygon_edge(
        self,
        frame: RailingFrame,
        direction_deg: float,
        num_lines: int,
    ) -> None:
        """
        **Feature: uniform-directional-generator-fix, Property 2: Even Distribution Across Polygon Extent**

        *For any* frame and direction, the first line SHALL be at or near the
        minimum of the valid line range.

        **Validates: Requirements 1.4, 2.1**
        """
        generator = UniformDirectionalGenerator()

        # Generate line pattern
        lines = generator._generate_line_pattern(frame, direction_deg, num_lines)

        # Calculate line and perpendicular directions
        angle_rad = math.radians(direction_deg)
        line_dx = math.sin(angle_rad)
        line_dy = math.cos(angle_rad)
        perp_dx = -math.cos(angle_rad)
        perp_dy = math.sin(angle_rad)

        # Get the valid line range
        line_direction = (line_dx, line_dy)
        perpendicular_direction = (perp_dx, perp_dy)
        min_proj, max_proj = generator._calculate_valid_line_range(
            frame.boundary, line_direction, perpendicular_direction
        )

        # Find the line with the minimum projection (first line)
        line_projections = [line.centroid.x * perp_dx + line.centroid.y * perp_dy for line in lines]
        first_line_proj = min(line_projections)

        # The first line should be at the minimum of the valid range
        # Allow small tolerance for floating point errors
        tolerance = (max_proj - min_proj) * 0.01  # 1% of extent
        assert math.isclose(first_line_proj, min_proj, abs_tol=max(tolerance, 0.01)), (
            f"First line projection {first_line_proj:.4f} should be at min extent {min_proj:.4f} "
            f"(tolerance={tolerance:.4f})"
        )

    @settings(max_examples=20, deadline=timedelta(seconds=2))
    @given(
        frame=valid_frame(),
        direction_deg=valid_direction_angle,
        num_lines=valid_num_lines,
    )
    def test_last_line_at_polygon_edge(
        self,
        frame: RailingFrame,
        direction_deg: float,
        num_lines: int,
    ) -> None:
        """
        **Feature: uniform-directional-generator-fix, Property 2: Even Distribution Across Polygon Extent**

        *For any* frame and direction, the last line SHALL be at or near the
        maximum of the valid line range.

        **Validates: Requirements 1.5, 2.1**
        """
        generator = UniformDirectionalGenerator()

        # Generate line pattern
        lines = generator._generate_line_pattern(frame, direction_deg, num_lines)

        # Calculate line and perpendicular directions
        angle_rad = math.radians(direction_deg)
        line_dx = math.sin(angle_rad)
        line_dy = math.cos(angle_rad)
        perp_dx = -math.cos(angle_rad)
        perp_dy = math.sin(angle_rad)

        # Get the valid line range
        line_direction = (line_dx, line_dy)
        perpendicular_direction = (perp_dx, perp_dy)
        min_proj, max_proj = generator._calculate_valid_line_range(
            frame.boundary, line_direction, perpendicular_direction
        )

        # Find the line with the maximum projection (last line)
        line_projections = [line.centroid.x * perp_dx + line.centroid.y * perp_dy for line in lines]
        last_line_proj = max(line_projections)

        # The last line should be at the maximum of the valid range
        # Allow small tolerance for floating point errors
        tolerance = (max_proj - min_proj) * 0.01  # 1% of extent
        assert math.isclose(last_line_proj, max_proj, abs_tol=max(tolerance, 0.01)), (
            f"Last line projection {last_line_proj:.4f} should be at max extent {max_proj:.4f} "
            f"(tolerance={tolerance:.4f})"
        )

    @settings(max_examples=20, deadline=timedelta(seconds=2))
    @given(
        frame=valid_frame(),
        direction_deg=valid_direction_angle,
        num_lines=valid_num_lines,
    )
    def test_lines_span_full_polygon_extent(
        self,
        frame: RailingFrame,
        direction_deg: float,
        num_lines: int,
    ) -> None:
        """
        **Feature: uniform-directional-generator-fix, Property 2: Even Distribution Across Polygon Extent**

        *For any* frame and direction, the lines SHALL span the full valid line range
        from minimum to maximum projection.

        **Validates: Requirements 1.3, 2.1, 2.3**
        """
        generator = UniformDirectionalGenerator()

        # Generate line pattern
        lines = generator._generate_line_pattern(frame, direction_deg, num_lines)

        # Calculate line and perpendicular directions
        angle_rad = math.radians(direction_deg)
        line_dx = math.sin(angle_rad)
        line_dy = math.cos(angle_rad)
        perp_dx = -math.cos(angle_rad)
        perp_dy = math.sin(angle_rad)

        # Get the valid line range
        line_direction = (line_dx, line_dy)
        perpendicular_direction = (perp_dx, perp_dy)
        min_proj, max_proj = generator._calculate_valid_line_range(
            frame.boundary, line_direction, perpendicular_direction
        )
        expected_range = max_proj - min_proj

        # Calculate the actual range covered by the lines
        line_projections = [line.centroid.x * perp_dx + line.centroid.y * perp_dy for line in lines]
        actual_range = max(line_projections) - min(line_projections)

        # The actual range should match the expected range
        # Allow 1% tolerance for floating point errors
        tolerance = expected_range * 0.01
        assert math.isclose(actual_range, expected_range, abs_tol=max(tolerance, 0.01)), (
            f"Lines span {actual_range:.4f} but valid range is {expected_range:.4f} "
            f"(tolerance={tolerance:.4f})"
        )

    @settings(max_examples=20, deadline=timedelta(seconds=2))
    @given(
        frame=valid_frame(),
        direction_deg=valid_direction_angle,
    )
    def test_single_line_at_center(
        self,
        frame: RailingFrame,
        direction_deg: float,
    ) -> None:
        """
        **Feature: uniform-directional-generator-fix, Property 2: Even Distribution Across Polygon Extent**

        *For any* frame and direction with a single line, the line SHALL be at
        the center of the valid line range.

        **Validates: Requirements 1.3, 2.1**
        """
        generator = UniformDirectionalGenerator()

        # Generate single line
        lines = generator._generate_line_pattern(frame, direction_deg, num_lines=1)

        assert len(lines) == 1, f"Expected 1 line, got {len(lines)}"

        # Calculate line and perpendicular directions
        angle_rad = math.radians(direction_deg)
        line_dx = math.sin(angle_rad)
        line_dy = math.cos(angle_rad)
        perp_dx = -math.cos(angle_rad)
        perp_dy = math.sin(angle_rad)

        # Get the valid line range
        line_direction = (line_dx, line_dy)
        perpendicular_direction = (perp_dx, perp_dy)
        min_proj, max_proj = generator._calculate_valid_line_range(
            frame.boundary, line_direction, perpendicular_direction
        )
        expected_center = (min_proj + max_proj) / 2.0

        # Get the line's projection
        line = lines[0]
        line_proj = line.centroid.x * perp_dx + line.centroid.y * perp_dy

        # The single line should be at the center
        tolerance = (max_proj - min_proj) * 0.01  # 1% of extent
        assert math.isclose(line_proj, expected_center, abs_tol=max(tolerance, 0.01)), (
            f"Single line projection {line_proj:.4f} should be at center {expected_center:.4f} "
            f"(tolerance={tolerance:.4f})"
        )
