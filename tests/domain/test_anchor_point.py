"""Tests for AnchorPoint model."""

import pytest
from shapely.geometry import Point

from railing_generator.domain.anchor_point import AnchorPoint


class TestAnchorPointCreation:
    """Tests for AnchorPoint creation with different position types."""

    def test_create_with_shapely_point(self) -> None:
        """Test creating AnchorPoint with Shapely Point."""
        anchor = AnchorPoint(
            position=Point(10.0, 20.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
        )
        assert anchor.position.x == 10.0
        assert anchor.position.y == 20.0
        assert isinstance(anchor.position, Point)

    def test_create_with_tuple(self) -> None:
        """Test creating AnchorPoint with tuple position."""
        anchor = AnchorPoint(
            position=(10.0, 20.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
        )
        assert anchor.position.x == 10.0
        assert anchor.position.y == 20.0
        assert isinstance(anchor.position, Point)

    def test_create_with_list(self) -> None:
        """Test creating AnchorPoint with list position."""
        anchor = AnchorPoint(
            position=[10.0, 20.0],
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
        )
        assert anchor.position.x == 10.0
        assert anchor.position.y == 20.0
        assert isinstance(anchor.position, Point)

    def test_invalid_position_raises_error(self) -> None:
        """Test that invalid position raises ValueError."""
        with pytest.raises(ValueError):
            AnchorPoint(
                position="invalid",  # type: ignore[arg-type]
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
            )


class TestAnchorPointSerialization:
    """Tests for AnchorPoint JSON serialization."""

    def test_serialize_to_dict(self) -> None:
        """Test serializing AnchorPoint to dict."""
        anchor = AnchorPoint(
            position=Point(10.0, 20.0),
            frame_segment_index=1,
            is_vertical_segment=True,
            frame_segment_angle_deg=5.0,
            layer=2,
            used=True,
        )
        data = anchor.model_dump()

        assert data["position"] == (10.0, 20.0)
        assert data["frame_segment_index"] == 1
        assert data["is_vertical_segment"] is True
        assert data["frame_segment_angle_deg"] == 5.0
        assert data["layer"] == 2
        assert data["used"] is True

    def test_serialize_to_json(self) -> None:
        """Test serializing AnchorPoint to JSON string."""
        anchor = AnchorPoint(
            position=Point(10.0, 20.0),
            frame_segment_index=0,
            is_vertical_segment=False,
            frame_segment_angle_deg=45.0,
        )
        json_str = anchor.model_dump_json()

        assert '"position":[10.0,20.0]' in json_str or '"position": [10.0, 20.0]' in json_str

    def test_deserialize_from_dict(self) -> None:
        """Test deserializing AnchorPoint from dict."""
        data = {
            "position": (15.0, 25.0),
            "frame_segment_index": 2,
            "is_vertical_segment": False,
            "frame_segment_angle_deg": -10.0,
            "layer": 3,
            "used": False,
        }
        anchor = AnchorPoint.model_validate(data)

        assert anchor.position.x == 15.0
        assert anchor.position.y == 25.0
        assert isinstance(anchor.position, Point)
        assert anchor.frame_segment_index == 2
        assert anchor.layer == 3

    def test_deserialize_from_json(self) -> None:
        """Test deserializing AnchorPoint from JSON string."""
        json_str = (
            '{"position": [30.0, 40.0], "frame_segment_index": 0, '
            '"is_vertical_segment": true, "frame_segment_angle_deg": 0.0}'
        )
        anchor = AnchorPoint.model_validate_json(json_str)

        assert anchor.position.x == 30.0
        assert anchor.position.y == 40.0
        assert isinstance(anchor.position, Point)

    def test_round_trip_serialization(self) -> None:
        """Test that serialization and deserialization preserves data."""
        original = AnchorPoint(
            position=Point(100.5, 200.5),
            frame_segment_index=3,
            is_vertical_segment=True,
            frame_segment_angle_deg=12.5,
            layer=1,
            used=True,
        )

        # Round trip through JSON
        json_str = original.model_dump_json()
        restored = AnchorPoint.model_validate_json(json_str)

        assert restored.position.x == original.position.x
        assert restored.position.y == original.position.y
        assert restored.frame_segment_index == original.frame_segment_index
        assert restored.is_vertical_segment == original.is_vertical_segment
        assert restored.frame_segment_angle_deg == original.frame_segment_angle_deg
        assert restored.layer == original.layer
        assert restored.used == original.used


class TestAnchorPointShapelyIntegration:
    """Tests for Shapely Point integration."""

    def test_position_has_shapely_methods(self) -> None:
        """Test that position supports Shapely Point methods."""
        anchor = AnchorPoint(
            position=Point(3.0, 4.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
        )

        # Test distance calculation
        other_point = Point(0.0, 0.0)
        distance = anchor.position.distance(other_point)
        assert distance == pytest.approx(5.0)  # 3-4-5 triangle

    def test_position_equals_comparison(self) -> None:
        """Test Point equality comparison."""
        anchor1 = AnchorPoint(
            position=Point(10.0, 20.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
        )
        anchor2 = AnchorPoint(
            position=(10.0, 20.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
        )

        assert anchor1.position.equals(anchor2.position)

    def test_position_coords_access(self) -> None:
        """Test accessing coordinates via coords property."""
        anchor = AnchorPoint(
            position=Point(5.0, 10.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
        )

        coords = list(anchor.position.coords)
        assert coords == [(5.0, 10.0)]
