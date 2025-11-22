"""Tests for RectangularRailingShape."""

import pytest
from shapely.geometry import Polygon

from railing_generator.domain.shapes.rectangular_railing_shape import (
    RectangularRailingShapeDefaults,
    RectangularRailingShapeParameters,
    RectangularRailingShape,
)


class TestRectangularRailingShapeDefaults:
    """Tests for RectangularRailingShapeDefaults dataclass."""

    def test_defaults_initialization(self) -> None:
        """Test that defaults can be initialized with expected values."""
        defaults = RectangularRailingShapeDefaults()
        assert defaults.width_cm == 200.0
        assert defaults.height_cm == 100.0
        assert defaults.frame_weight_per_meter_kg_m == 0.5

    def test_defaults_custom_values(self) -> None:
        """Test that defaults can be initialized with custom values."""
        defaults = RectangularRailingShapeDefaults(
            width_cm=300.0,
            height_cm=150.0,
            frame_weight_per_meter_kg_m=0.8,
        )
        assert defaults.width_cm == 300.0
        assert defaults.height_cm == 150.0
        assert defaults.frame_weight_per_meter_kg_m == 0.8


class TestRectangularRailingShapeParameters:
    """Tests for RectangularRailingShapeParameters Pydantic model."""

    def test_parameters_initialization(self) -> None:
        """Test that parameters can be initialized with valid values."""
        params = RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )
        assert params.width_cm == 200.0
        assert params.height_cm == 100.0
        assert params.frame_weight_per_meter_kg_m == 0.5

    def test_parameters_validation_positive_width(self) -> None:
        """Test that width must be positive."""
        with pytest.raises(ValueError):
            RectangularRailingShapeParameters(
                width_cm=0.0,
                height_cm=100.0,
                frame_weight_per_meter_kg_m=0.5,
            )

        with pytest.raises(ValueError):
            RectangularRailingShapeParameters(
                width_cm=-10.0,
                height_cm=100.0,
                frame_weight_per_meter_kg_m=0.5,
            )

    def test_parameters_validation_positive_height(self) -> None:
        """Test that height must be positive."""
        with pytest.raises(ValueError):
            RectangularRailingShapeParameters(
                width_cm=200.0,
                height_cm=0.0,
                frame_weight_per_meter_kg_m=0.5,
            )

        with pytest.raises(ValueError):
            RectangularRailingShapeParameters(
                width_cm=200.0,
                height_cm=-10.0,
                frame_weight_per_meter_kg_m=0.5,
            )

    def test_parameters_validation_positive_weight(self) -> None:
        """Test that weight per meter must be positive."""
        with pytest.raises(ValueError):
            RectangularRailingShapeParameters(
                width_cm=200.0,
                height_cm=100.0,
                frame_weight_per_meter_kg_m=0.0,
            )

        with pytest.raises(ValueError):
            RectangularRailingShapeParameters(
                width_cm=200.0,
                height_cm=100.0,
                frame_weight_per_meter_kg_m=-0.5,
            )

    def test_from_defaults(self) -> None:
        """Test creating parameters from defaults."""
        defaults = RectangularRailingShapeDefaults(
            width_cm=300.0,
            height_cm=150.0,
            frame_weight_per_meter_kg_m=0.8,
        )
        params = RectangularRailingShapeParameters.from_defaults(defaults)
        assert params.width_cm == 300.0
        assert params.height_cm == 150.0
        assert params.frame_weight_per_meter_kg_m == 0.8


class TestRectangularRailingShape:
    """Tests for RectangularRailingShape."""

    def test_initialization(self) -> None:
        """Test that shape can be initialized with parameters."""
        params = RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = RectangularRailingShape(params)
        assert shape.params == params

    def test_generate_frame_returns_frame(self) -> None:
        """Test that generate_frame returns a RailingFrame."""
        params = RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = RectangularRailingShape(params)
        frame = shape.generate_frame()
        assert frame is not None
        assert len(frame.rods) == 4  # 4 sides

    def test_generate_frame_rod_count(self) -> None:
        """Test that frame has exactly 4 rods (4 sides)."""
        params = RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = RectangularRailingShape(params)
        frame = shape.generate_frame()
        assert len(frame.rods) == 4

    def test_generate_frame_all_rods_layer_zero(self) -> None:
        """Test that all frame rods are on layer 0."""
        params = RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = RectangularRailingShape(params)
        frame = shape.generate_frame()
        for rod in frame.rods:
            assert rod.layer == 0

    def test_generate_frame_boundary_is_closed(self) -> None:
        """Test that the frame boundary forms a closed polygon."""
        params = RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = RectangularRailingShape(params)
        frame = shape.generate_frame()
        assert isinstance(frame.boundary, Polygon)
        assert frame.boundary.is_valid
        assert not frame.boundary.is_empty

    def test_generate_frame_boundary_area(self) -> None:
        """Test that the boundary area matches width * height."""
        params = RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = RectangularRailingShape(params)
        frame = shape.generate_frame()
        expected_area = 200.0 * 100.0
        assert abs(frame.boundary.area - expected_area) < 0.01

    def test_generate_frame_total_length(self) -> None:
        """Test that total frame length is perimeter (2 * width + 2 * height)."""
        params = RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = RectangularRailingShape(params)
        frame = shape.generate_frame()
        expected_length = 2 * 200.0 + 2 * 100.0  # 600.0 cm
        assert abs(frame.total_length_cm - expected_length) < 0.01

    def test_generate_frame_total_weight(self) -> None:
        """Test that total weight is calculated correctly."""
        params = RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = RectangularRailingShape(params)
        frame = shape.generate_frame()
        # Total length = 600 cm = 6 m
        # Weight = 6 m * 0.5 kg/m = 3.0 kg
        expected_weight = 3.0
        assert abs(frame.total_weight_kg - expected_weight) < 0.01

    def test_generate_frame_different_dimensions(self) -> None:
        """Test frame generation with different dimensions."""
        params = RectangularRailingShapeParameters(
            width_cm=300.0,
            height_cm=150.0,
            frame_weight_per_meter_kg_m=0.8,
        )
        shape = RectangularRailingShape(params)
        frame = shape.generate_frame()

        # Check area
        expected_area = 300.0 * 150.0
        assert abs(frame.boundary.area - expected_area) < 0.01

        # Check perimeter
        expected_length = 2 * 300.0 + 2 * 150.0  # 900.0 cm
        assert abs(frame.total_length_cm - expected_length) < 0.01

        # Check weight (900 cm = 9 m, 9 * 0.8 = 7.2 kg)
        expected_weight = 7.2
        assert abs(frame.total_weight_kg - expected_weight) < 0.01

    def test_generate_frame_rods_form_rectangle(self) -> None:
        """Test that rods form a proper rectangle with correct corners."""
        params = RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = RectangularRailingShape(params)
        frame = shape.generate_frame()

        # Expected corners (counterclockwise from origin)
        expected_corners = [
            (0.0, 0.0),  # Bottom-left
            (200.0, 0.0),  # Bottom-right
            (200.0, 100.0),  # Top-right
            (0.0, 100.0),  # Top-left
        ]

        # Extract boundary coordinates (Polygon exterior)
        boundary_coords = list(frame.boundary.exterior.coords)

        # Check that all expected corners are in the boundary
        for corner in expected_corners:
            assert corner in boundary_coords

    def test_generate_frame_immutability(self) -> None:
        """Test that generated frame is immutable."""
        params = RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = RectangularRailingShape(params)
        frame = shape.generate_frame()

        # Attempt to modify should raise error
        with pytest.raises(Exception):  # Pydantic raises ValidationError
            frame.rods = []
