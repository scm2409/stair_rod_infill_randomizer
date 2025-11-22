"""Tests for RailingFrame class."""

import pytest
from pydantic import ValidationError
from shapely.geometry import LineString

from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.rod import Rod


def create_closed_rectangular_frame(
    width: float = 100.0, height: float = 100.0, weight_kg_m: float = 0.5
) -> list[Rod]:
    """Helper to create a closed rectangular frame."""
    return [
        Rod(
            geometry=LineString([(0, 0), (0, height)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=weight_kg_m,
            layer=0,
        ),
        Rod(
            geometry=LineString([(0, height), (width, height)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=weight_kg_m,
            layer=0,
        ),
        Rod(
            geometry=LineString([(width, height), (width, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=weight_kg_m,
            layer=0,
        ),
        Rod(
            geometry=LineString([(width, 0), (0, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=weight_kg_m,
            layer=0,
        ),
    ]


class TestRailingFrameCreation:
    """Test RailingFrame creation and validation."""

    def test_create_stair_frame(self) -> None:
        """Test creating a valid RailingFrame with closed boundary."""
        # Create a closed rectangular frame
        rods = [
            Rod(
                geometry=LineString([(0, 0), (0, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=0,
            ),
            Rod(
                geometry=LineString([(0, 100), (100, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=0,
            ),
            Rod(
                geometry=LineString([(100, 100), (100, 0)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=0,
            ),
            Rod(
                geometry=LineString([(100, 0), (0, 0)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=0,
            ),
        ]

        frame = RailingFrame(rods=rods)

        assert frame.rods == rods
        assert frame.boundary.is_valid
        assert frame.rod_count == 4

    def test_create_stair_frame_empty_rods(self) -> None:
        """Test that accessing boundary with empty rods list raises error."""
        frame = RailingFrame(rods=[])

        # Boundary is computed lazily, so error occurs when accessing it
        with pytest.raises(ValueError, match="Expected exactly 1 polygon"):
            _ = frame.boundary


class TestRailingFrameImmutability:
    """Test that RailingFrame is immutable."""

    def test_cannot_modify_rods(self) -> None:
        """Test that rods list cannot be modified after creation."""
        rods = [
            Rod(
                geometry=LineString([(0, 0), (0, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=0,
            ),
            Rod(
                geometry=LineString([(0, 100), (100, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=0,
            ),
            Rod(
                geometry=LineString([(100, 100), (100, 0)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=0,
            ),
            Rod(
                geometry=LineString([(100, 0), (0, 0)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=0,
            ),
        ]
        frame = RailingFrame(rods=rods)

        with pytest.raises(ValidationError):
            frame.rods = []


class TestRailingFrameComputedFields:
    """Test computed fields of RailingFrame."""

    def test_total_length_cm(self) -> None:
        """Test total_length_cm calculation."""
        rods = create_closed_rectangular_frame(width=100.0, height=100.0, weight_kg_m=0.5)
        frame = RailingFrame(rods=rods)

        # 4 sides of 100cm each = 400cm total
        assert frame.total_length_cm == pytest.approx(400.0)

    def test_total_weight_kg(self) -> None:
        """Test total_weight_kg calculation."""
        rods = create_closed_rectangular_frame(width=100.0, height=100.0, weight_kg_m=0.5)
        frame = RailingFrame(rods=rods)

        # Each rod: 100cm * 0.5 kg/m = 0.5 kg
        # Total: 4 * 0.5 = 2.0 kg
        assert frame.total_weight_kg == pytest.approx(2.0)

    def test_total_weight_kg_different_weights(self) -> None:
        """Test total_weight_kg with different rod weights."""
        # Create frame with mixed weights
        rods = [
            Rod(
                geometry=LineString([(0, 0), (0, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=0,
            ),
            Rod(
                geometry=LineString([(0, 100), (100, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=1.0,
                layer=0,
            ),
            Rod(
                geometry=LineString([(100, 100), (100, 0)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=0,
            ),
            Rod(
                geometry=LineString([(100, 0), (0, 0)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=1.0,
                layer=0,
            ),
        ]
        frame = RailingFrame(rods=rods)

        # Rod 1: 100cm * 0.5 kg/m = 0.5 kg
        # Rod 2: 100cm * 1.0 kg/m = 1.0 kg
        # Rod 3: 100cm * 0.5 kg/m = 0.5 kg
        # Rod 4: 100cm * 1.0 kg/m = 1.0 kg
        # Total: 3.0 kg
        assert frame.total_weight_kg == pytest.approx(3.0)

    def test_rod_count(self) -> None:
        """Test rod_count property."""
        rods = create_closed_rectangular_frame()
        frame = RailingFrame(rods=rods)

        assert frame.rod_count == 4


class TestRailingFrameSerialization:
    """Test RailingFrame serialization."""

    def test_model_dump_includes_boundary(self) -> None:
        """Test that model_dump includes computed boundary."""
        rods = create_closed_rectangular_frame()
        frame = RailingFrame(rods=rods)
        data = frame.model_dump()

        assert "boundary" in data  # Computed field is included
        assert "rods" in data

    def test_model_dump_geometry_includes_all(self) -> None:
        """Test that model_dump_geometry includes geometry data."""
        rods = create_closed_rectangular_frame()
        frame = RailingFrame(rods=rods)
        data = frame.model_dump_geometry()

        assert "rods" in data
        assert "boundary" in data
        assert isinstance(data["rods"], list)
        assert len(data["rods"]) == 4
        assert "geometry" in data["rods"][0]
        assert isinstance(data["boundary"], list)

    def test_model_dump_geometry_boundary_coordinates(self) -> None:
        """Test that boundary coordinates are correctly serialized."""
        rods = create_closed_rectangular_frame(width=100.0, height=100.0)
        frame = RailingFrame(rods=rods)
        data = frame.model_dump_geometry()

        boundary_coords = data["boundary"]
        assert isinstance(boundary_coords, list)
        assert len(boundary_coords) == 5  # Polygon is closed
        # Check that we have a closed polygon (first == last)
        assert boundary_coords[0] == boundary_coords[-1]
