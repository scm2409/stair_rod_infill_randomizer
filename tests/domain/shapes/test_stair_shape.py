"""Tests for StairShape."""

import pytest
from pydantic import ValidationError
from shapely.geometry import Polygon

from railing_generator.domain.shapes.stair_shape import (
    StairShape,
    StairShapeDefaults,
    StairShapeParameters,
)


class TestStairShapeDefaults:
    """Test StairShapeDefaults dataclass."""

    def test_create_defaults(self) -> None:
        """Test creating defaults with default values."""
        defaults = StairShapeDefaults()

        assert defaults.post_length_cm == 150.0
        assert defaults.stair_width_cm == 280.0
        assert defaults.stair_height_cm == 280.0
        assert defaults.num_steps == 10
        assert defaults.frame_weight_per_meter_kg_m == 0.5

    def test_create_defaults_with_custom_values(self) -> None:
        """Test creating defaults with custom values."""
        defaults = StairShapeDefaults(
            post_length_cm=200.0,
            stair_width_cm=250.0,
            stair_height_cm=300.0,
            num_steps=15,
            frame_weight_per_meter_kg_m=0.7,
        )

        assert defaults.post_length_cm == 200.0
        assert defaults.stair_width_cm == 250.0
        assert defaults.stair_height_cm == 300.0
        assert defaults.num_steps == 15
        assert defaults.frame_weight_per_meter_kg_m == 0.7


class TestStairShapeParameters:
    """Test StairShapeParameters Pydantic model."""

    def test_create_valid_parameters(self) -> None:
        """Test creating valid parameters."""
        params = StairShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )

        assert params.post_length_cm == 150.0
        assert params.stair_width_cm == 280.0
        assert params.stair_height_cm == 280.0
        assert params.num_steps == 10
        assert params.frame_weight_per_meter_kg_m == 0.5

    def test_from_defaults(self) -> None:
        """Test creating parameters from defaults."""
        defaults = StairShapeDefaults(
            post_length_cm=200.0,
            stair_width_cm=250.0,
            stair_height_cm=300.0,
            num_steps=12,
            frame_weight_per_meter_kg_m=0.6,
        )

        params = StairShapeParameters.from_defaults(defaults)

        assert params.post_length_cm == 200.0
        assert params.stair_width_cm == 250.0
        assert params.stair_height_cm == 300.0
        assert params.num_steps == 12
        assert params.frame_weight_per_meter_kg_m == 0.6

    def test_post_length_must_be_positive(self) -> None:
        """Test that post_length_cm must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            StairShapeParameters(
                post_length_cm=0.0,
                stair_width_cm=280.0,
                stair_height_cm=280.0,
                num_steps=10,
                frame_weight_per_meter_kg_m=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("post_length_cm",) for e in errors)

    def test_stair_width_must_be_positive(self) -> None:
        """Test that stair_width_cm must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            StairShapeParameters(
                post_length_cm=150.0,
                stair_width_cm=0.0,
                stair_height_cm=280.0,
                num_steps=10,
                frame_weight_per_meter_kg_m=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("stair_width_cm",) for e in errors)

    def test_stair_height_must_be_positive(self) -> None:
        """Test that stair_height_cm must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            StairShapeParameters(
                post_length_cm=150.0,
                stair_width_cm=280.0,
                stair_height_cm=-10.0,
                num_steps=10,
                frame_weight_per_meter_kg_m=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("stair_height_cm",) for e in errors)

    def test_num_steps_minimum(self) -> None:
        """Test that num_steps must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            StairShapeParameters(
                post_length_cm=150.0,
                stair_width_cm=280.0,
                stair_height_cm=280.0,
                num_steps=0,
                frame_weight_per_meter_kg_m=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("num_steps",) for e in errors)

    def test_num_steps_maximum(self) -> None:
        """Test that num_steps cannot exceed 50."""
        with pytest.raises(ValidationError) as exc_info:
            StairShapeParameters(
                post_length_cm=150.0,
                stair_width_cm=280.0,
                stair_height_cm=280.0,
                num_steps=51,
                frame_weight_per_meter_kg_m=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("num_steps",) for e in errors)

    def test_frame_weight_must_be_positive(self) -> None:
        """Test that frame_weight_per_meter_kg_m must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            StairShapeParameters(
                post_length_cm=150.0,
                stair_width_cm=280.0,
                stair_height_cm=280.0,
                num_steps=10,
                frame_weight_per_meter_kg_m=0.0,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("frame_weight_per_meter_kg_m",) for e in errors)

    def test_step_width_calculated(self) -> None:
        """Test that step_width_cm is calculated correctly."""
        params = StairShapeParameters(
            post_length_cm=100.0,
            stair_width_cm=120.0,
            stair_height_cm=80.0,
            num_steps=4,
            frame_weight_per_meter_kg_m=0.5,
        )

        assert params.step_width_cm == pytest.approx(30.0)

    def test_step_height_calculated(self) -> None:
        """Test that step_height_cm is calculated correctly."""
        params = StairShapeParameters(
            post_length_cm=100.0,
            stair_width_cm=120.0,
            stair_height_cm=80.0,
            num_steps=4,
            frame_weight_per_meter_kg_m=0.5,
        )

        assert params.step_height_cm == pytest.approx(20.0)

    def test_step_dimensions_with_different_values(self) -> None:
        """Test step dimensions with different parameter values."""
        params = StairShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )

        assert params.step_width_cm == pytest.approx(28.0)
        assert params.step_height_cm == pytest.approx(28.0)


class TestStairShapeCreation:
    """Test StairShape creation."""

    def test_create_stair_shape(self) -> None:
        """Test creating a stair shape."""
        params = StairShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )

        shape = StairShape(params)

        assert shape.params == params


class TestStairShapeBoundary:
    """Test StairShape boundary calculation."""

    def test_get_boundary_returns_polygon(self) -> None:
        """Test that get_boundary returns a Polygon."""
        params = StairShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = StairShape(params)

        boundary = shape.get_boundary()

        assert isinstance(boundary, Polygon)
        assert boundary.is_valid

    def test_boundary_is_closed(self) -> None:
        """Test that boundary polygon is closed."""
        params = StairShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = StairShape(params)

        boundary = shape.get_boundary()

        # First and last coordinates should be the same
        coords = list(boundary.exterior.coords)
        assert coords[0] == coords[-1]

    def test_boundary_corners(self) -> None:
        """Test that boundary has correct corner points."""
        params = StairShapeParameters(
            post_length_cm=100.0,
            stair_width_cm=200.0,
            stair_height_cm=200.0,
            num_steps=5,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = StairShape(params)

        boundary = shape.get_boundary()
        coords = list(boundary.exterior.coords)

        # Check key corners
        assert (0.0, 0.0) in coords  # Bottom-left (base of left post)
        assert (0.0, 100.0) in coords  # Top-left (top of left post)
        assert (
            200.0,
            300.0,
        ) in coords  # Top-right (top of right post = post_length + stair_height)
        # Right post ends at stair_height (base of right post)
        assert (200.0, 200.0) in coords  # Bottom of right post


class TestStairShapeFrameRods:
    """Test StairShape frame rod generation."""

    def test_get_frame_rods_returns_list(self) -> None:
        """Test that get_frame_rods returns a list."""
        params = StairShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = StairShape(params)

        rods = shape.get_frame_rods()

        assert isinstance(rods, list)
        assert len(rods) > 0

    def test_frame_rods_have_layer_zero(self) -> None:
        """Test that all frame rods have layer 0."""
        params = StairShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = StairShape(params)

        rods = shape.get_frame_rods()

        assert all(rod.layer == 0 for rod in rods)

    def test_frame_rods_have_correct_weight(self) -> None:
        """Test that frame rods have correct weight per meter."""
        params = StairShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.7,
        )
        shape = StairShape(params)

        rods = shape.get_frame_rods()

        assert all(rod.weight_kg_m == 0.7 for rod in rods)

    def test_frame_has_posts_and_handrail(self) -> None:
        """Test that frame includes posts and handrail."""
        params = StairShapeParameters(
            post_length_cm=100.0,
            stair_width_cm=200.0,
            stair_height_cm=200.0,
            num_steps=5,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = StairShape(params)

        rods = shape.get_frame_rods()

        # Should have at least: left post, handrail, right post, and step segments
        assert len(rods) >= 3


class TestStairShapeExactGeometry:
    """Test exact geometry coordinates for a simple staircase."""

    def test_simple_staircase_exact_coordinates(self) -> None:
        """
        Test exact coordinates for a simple staircase.

        Parameters:
        - post_length_cm: 100
        - stair_width_cm: 120 (horizontal distance between posts)
        - stair_height_cm: 80 (vertical distance between post bases)
        - num_steps: 4
        - This gives us: step_width = 120/4 = 30cm, step_height = 80/4 = 20cm

        Expected geometry (counterclockwise from bottom-left):
        1. Left post: (0, 0) -> (0, 100)
        2. Handrail: (0, 100) -> (120, 180) [angled, rises by stair_height]
        3. Right post: (120, 180) -> (120, 80) [ends at stair_height]
        4. Steps going left (4 steps, each 30cm wide and 20cm high):
           - Step 4 (highest): (120, 60) -> (90, 60) [horizontal]
           - Riser: (90, 60) -> (90, 40) [vertical down]
           - Step 3: (90, 40) -> (60, 40) [horizontal]
           - Riser: (60, 40) -> (60, 20) [vertical down]
           - Step 2: (60, 20) -> (30, 20) [horizontal]
           - Riser: (30, 20) -> (30, 0) [vertical down]
           - Step 1 (lowest): (30, 0) -> (0, 0) [horizontal, closes loop]
        """
        params = StairShapeParameters(
            post_length_cm=100.0,
            stair_width_cm=120.0,
            stair_height_cm=80.0,
            num_steps=4,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = StairShape(params)

        # Get boundary from the single source of truth
        boundary = shape.get_boundary()
        coords = list(boundary.exterior.coords)

        # Expected coordinates in order (counterclockwise)
        expected_coords = [
            (0.0, 0.0),  # Start: bottom-left
            (0.0, 100.0),  # Top of left post
            (120.0, 180.0),  # Top of right post (100 + 80)
            (120.0, 80.0),  # Bottom of right post (at stair_height)
            (120.0, 60.0),  # Riser down to top of highest step (step 4 at 3*20=60)
            (90.0, 60.0),  # Step 4 horizontal
            (90.0, 40.0),  # Riser down
            (60.0, 40.0),  # Step 3 horizontal
            (60.0, 20.0),  # Riser down
            (30.0, 20.0),  # Step 2 horizontal
            (30.0, 0.0),  # Riser down
            (0.0, 0.0),  # Step 1 horizontal (closes loop)
        ]

        # Verify we have the expected number of coordinates
        assert len(coords) == len(expected_coords), (
            f"Expected {len(expected_coords)} coordinates, got {len(coords)}"
        )

        # Verify each coordinate matches exactly
        for i, (actual, expected) in enumerate(zip(coords, expected_coords)):
            assert actual == pytest.approx(expected), (
                f"Coordinate {i}: expected {expected}, got {actual}"
            )

        # Verify the boundary is valid
        assert boundary.is_valid
