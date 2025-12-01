"""Tests for AnchorPointFinder class."""

import pytest
from shapely.geometry import Point

from railing_generator.domain.anchor_point import AnchorPoint
from railing_generator.domain.anchor_point_finder import AnchorPointFinder


class TestAnchorPointFinderInit:
    """Tests for AnchorPointFinder initialization."""

    def test_default_search_radius(self) -> None:
        """Test default search radius is 10.0 cm."""
        finder = AnchorPointFinder()
        assert finder.search_radius_cm == 10.0

    def test_custom_search_radius(self) -> None:
        """Test custom search radius is set correctly."""
        finder = AnchorPointFinder(search_radius_cm=15.0)
        assert finder.search_radius_cm == 15.0

    def test_invalid_search_radius_zero(self) -> None:
        """Test that zero search radius raises ValueError."""
        with pytest.raises(ValueError, match="search_radius_cm must be positive"):
            AnchorPointFinder(search_radius_cm=0.0)

    def test_invalid_search_radius_negative(self) -> None:
        """Test that negative search radius raises ValueError."""
        with pytest.raises(ValueError, match="search_radius_cm must be positive"):
            AnchorPointFinder(search_radius_cm=-5.0)


class TestFindNearestUnconnected:
    """Tests for find_nearest_unconnected method."""

    @pytest.fixture
    def finder(self) -> AnchorPointFinder:
        """Create a finder with 10.0 cm search radius."""
        return AnchorPointFinder(search_radius_cm=10.0)

    @pytest.fixture
    def sample_anchors(self) -> list[AnchorPoint]:
        """Create sample anchor points for testing."""
        return [
            AnchorPoint(
                position=Point(0.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
            AnchorPoint(
                position=Point(5.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
            AnchorPoint(
                position=Point(15.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
            AnchorPoint(
                position=Point(3.0, 4.0),  # Distance 5.0 from origin
                frame_segment_index=1,
                is_vertical_segment=False,
                frame_segment_angle_deg=45.0,
                layer=2,
                used=True,  # Connected
            ),
        ]

    def test_empty_anchor_list(self, finder: AnchorPointFinder) -> None:
        """Test with empty anchor list returns None."""
        result = finder.find_nearest_unconnected(Point(0.0, 0.0), [])
        assert result is None

    def test_finds_nearest_unconnected(
        self, finder: AnchorPointFinder, sample_anchors: list[AnchorPoint]
    ) -> None:
        """Test finds the nearest unconnected anchor."""
        result = finder.find_nearest_unconnected(Point(4.0, 0.0), sample_anchors)
        assert result is not None
        assert result.position.equals(Point(5.0, 0.0))

    def test_skips_connected_anchors(
        self, finder: AnchorPointFinder, sample_anchors: list[AnchorPoint]
    ) -> None:
        """Test that connected (used) anchors are skipped."""
        # Search near the connected anchor at (3.0, 4.0)
        # Distance from (3.0, 4.0) to (0.0, 0.0) = 5.0
        # Distance from (3.0, 4.0) to (5.0, 0.0) = sqrt(4 + 16) = sqrt(20) ≈ 4.47
        # So (5.0, 0.0) is actually closer
        result = finder.find_nearest_unconnected(Point(3.0, 4.0), sample_anchors)
        # Should find (5.0, 0.0) which is ~4.47 away, not the connected one at (3.0, 4.0)
        assert result is not None
        assert result.position.equals(Point(5.0, 0.0))
        # Verify the connected anchor was skipped (it would be at distance 0)
        assert result.used is False

    def test_respects_search_radius(
        self, finder: AnchorPointFinder, sample_anchors: list[AnchorPoint]
    ) -> None:
        """Test that anchors outside search radius are not found."""
        # Search from (20.0, 0.0) - only (15.0, 0.0) is within 10.0 cm
        result = finder.find_nearest_unconnected(Point(20.0, 0.0), sample_anchors)
        assert result is not None
        assert result.position.equals(Point(15.0, 0.0))

    def test_no_anchors_within_radius(self, finder: AnchorPointFinder) -> None:
        """Test returns None when no anchors within radius."""
        anchors = [
            AnchorPoint(
                position=Point(100.0, 100.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
        ]
        result = finder.find_nearest_unconnected(Point(0.0, 0.0), anchors)
        assert result is None

    def test_all_anchors_connected(self, finder: AnchorPointFinder) -> None:
        """Test returns None when all anchors are connected."""
        anchors = [
            AnchorPoint(
                position=Point(1.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=True,
            ),
            AnchorPoint(
                position=Point(2.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=True,
            ),
        ]
        result = finder.find_nearest_unconnected(Point(0.0, 0.0), anchors)
        assert result is None

    def test_exact_position_match(self, finder: AnchorPointFinder) -> None:
        """Test finding anchor at exact search position."""
        anchors = [
            AnchorPoint(
                position=Point(5.0, 5.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
        ]
        result = finder.find_nearest_unconnected(Point(5.0, 5.0), anchors)
        assert result is not None
        assert result.position.equals(Point(5.0, 5.0))

    def test_anchor_at_exact_radius_boundary(self, finder: AnchorPointFinder) -> None:
        """Test anchor exactly at search radius boundary is included."""
        anchors = [
            AnchorPoint(
                position=Point(10.0, 0.0),  # Exactly 10.0 cm from origin
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
        ]
        result = finder.find_nearest_unconnected(Point(0.0, 0.0), anchors)
        assert result is not None
        assert result.position.equals(Point(10.0, 0.0))


class TestFindAllUnconnectedWithinRadius:
    """Tests for find_all_unconnected_within_radius method."""

    @pytest.fixture
    def finder(self) -> AnchorPointFinder:
        """Create a finder with 10.0 cm search radius."""
        return AnchorPointFinder(search_radius_cm=10.0)

    def test_empty_anchor_list(self, finder: AnchorPointFinder) -> None:
        """Test with empty anchor list returns empty list."""
        result = finder.find_all_unconnected_within_radius(Point(0.0, 0.0), [])
        assert result == []

    def test_finds_all_within_radius(self, finder: AnchorPointFinder) -> None:
        """Test finds all unconnected anchors within radius."""
        anchors = [
            AnchorPoint(
                position=Point(3.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
            AnchorPoint(
                position=Point(5.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
            AnchorPoint(
                position=Point(8.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
        ]
        result = finder.find_all_unconnected_within_radius(Point(0.0, 0.0), anchors)
        assert len(result) == 3
        # Should be sorted by distance
        assert result[0][0].position.equals(Point(3.0, 0.0))
        assert result[1][0].position.equals(Point(5.0, 0.0))
        assert result[2][0].position.equals(Point(8.0, 0.0))

    def test_returns_distances(self, finder: AnchorPointFinder) -> None:
        """Test that distances are returned correctly."""
        anchors = [
            AnchorPoint(
                position=Point(3.0, 4.0),  # Distance 5.0 from origin
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
        ]
        result = finder.find_all_unconnected_within_radius(Point(0.0, 0.0), anchors)
        assert len(result) == 1
        assert result[0][1] == pytest.approx(5.0)

    def test_skips_connected_anchors(self, finder: AnchorPointFinder) -> None:
        """Test that connected anchors are excluded."""
        anchors = [
            AnchorPoint(
                position=Point(1.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=True,  # Connected
            ),
            AnchorPoint(
                position=Point(2.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
        ]
        result = finder.find_all_unconnected_within_radius(Point(0.0, 0.0), anchors)
        assert len(result) == 1
        assert result[0][0].position.equals(Point(2.0, 0.0))
