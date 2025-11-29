"""Tests for anchor point frame segment angle and rod cut angle calculation."""

import pytest
from shapely.geometry import LineString

from railing_generator.domain.anchor_point import AnchorPoint
from railing_generator.domain.infill_generators.random_generator_v2 import RandomGeneratorV2
from railing_generator.domain.rod import Rod


class TestAnchorPointFrameSegmentAngle:
    """Test that anchor points store frame segment angles."""

    def test_anchor_point_has_frame_segment_angle(self) -> None:
        """Test that AnchorPoint includes frame_segment_angle_deg field."""
        anchor = AnchorPoint(
            position=(10.0, 20.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=5.0,
        )

        assert anchor.frame_segment_angle_deg == 5.0

    def test_anchor_point_frame_segment_angle_required(self) -> None:
        """Test that frame_segment_angle_deg is a required field."""
        with pytest.raises(Exception):  # Pydantic validation error
            AnchorPoint(
                position=(10.0, 20.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                # Missing frame_segment_angle_deg
            )


class TestCutAngleCalculation:
    """Test cut angle calculation based on rod and frame segment angles."""

    def test_calculate_cut_angles_vertical_rod_vertical_frame(self) -> None:
        """Test cut angles when both rod and frame are vertical (0°)."""
        generator = RandomGeneratorV2()

        start_anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
        )

        end_anchor = AnchorPoint(
            position=(0.0, 100.0),
            frame_segment_index=1,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
        )

        # Rod angle is 0° (vertical)
        rod_angle = 0.0

        start_cut, end_cut = generator._calculate_cut_angles(
            rod_angle_deg=rod_angle,
            start_anchor=start_anchor,
            end_anchor=end_anchor,
        )

        # Both should be 0° since rod and frame are parallel
        assert start_cut == 0.0
        assert end_cut == 0.0

    def test_calculate_cut_angles_angled_rod_vertical_frame(self) -> None:
        """Test cut angles when rod is angled but frame is vertical."""
        generator = RandomGeneratorV2()

        start_anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
        )

        end_anchor = AnchorPoint(
            position=(0.0, 100.0),
            frame_segment_index=1,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
        )

        # Rod angle is 15° from vertical
        rod_angle = 15.0

        start_cut, end_cut = generator._calculate_cut_angles(
            rod_angle_deg=rod_angle,
            start_anchor=start_anchor,
            end_anchor=end_anchor,
        )

        # Both should be 15° since frame is vertical (0°)
        assert start_cut == 15.0
        assert end_cut == 15.0

    def test_calculate_cut_angles_vertical_rod_angled_frame(self) -> None:
        """Test cut angles when rod is vertical but frame is angled."""
        generator = RandomGeneratorV2()

        start_anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=False,
            frame_segment_angle_deg=10.0,
        )

        end_anchor = AnchorPoint(
            position=(0.0, 100.0),
            frame_segment_index=1,
            is_vertical_segment=False,
            frame_segment_angle_deg=-10.0,
        )

        # Rod angle is 0° (vertical)
        rod_angle = 0.0

        start_cut, end_cut = generator._calculate_cut_angles(
            rod_angle_deg=rod_angle,
            start_anchor=start_anchor,
            end_anchor=end_anchor,
        )

        # Start: 0° - 10° = -10°
        # End: 0° - (-10°) = 10°
        assert start_cut == -10.0
        assert end_cut == 10.0

    def test_calculate_cut_angles_both_angled(self) -> None:
        """Test cut angles when both rod and frame segments are angled."""
        generator = RandomGeneratorV2()

        start_anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=False,
            frame_segment_angle_deg=20.0,
        )

        end_anchor = AnchorPoint(
            position=(0.0, 100.0),
            frame_segment_index=1,
            is_vertical_segment=False,
            frame_segment_angle_deg=-15.0,
        )

        # Rod angle is 25° from vertical
        rod_angle = 25.0

        start_cut, end_cut = generator._calculate_cut_angles(
            rod_angle_deg=rod_angle,
            start_anchor=start_anchor,
            end_anchor=end_anchor,
        )

        # Start: 25° - 20° = 5°
        # End: 25° - (-15°) = 40°
        assert start_cut == 5.0
        assert end_cut == 40.0

    def test_calculate_cut_angles_normalized_to_range(self) -> None:
        """Test that cut angles are normalized to [-90, 90] range."""
        generator = RandomGeneratorV2()

        start_anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=False,
            frame_segment_angle_deg=-80.0,
        )

        end_anchor = AnchorPoint(
            position=(0.0, 100.0),
            frame_segment_index=1,
            is_vertical_segment=False,
            frame_segment_angle_deg=80.0,
        )

        # Rod angle is 50° from vertical
        rod_angle = 50.0

        start_cut, end_cut = generator._calculate_cut_angles(
            rod_angle_deg=rod_angle,
            start_anchor=start_anchor,
            end_anchor=end_anchor,
        )

        # Start: 50° - (-80°) = 130° -> normalized to 50° (180 - 130)
        # End: 50° - 80° = -30°
        assert start_cut == 50.0
        assert end_cut == -30.0

        # Both should be within valid range
        assert -90.0 <= start_cut <= 90.0
        assert -90.0 <= end_cut <= 90.0

    def test_calculate_cut_angles_extreme_case_1(self) -> None:
        """Test normalization with extreme angle differences."""
        generator = RandomGeneratorV2()

        # Horizontal frame segment (90°) with vertical rod (0°)
        start_anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=False,
            frame_segment_angle_deg=90.0,
        )

        end_anchor = AnchorPoint(
            position=(0.0, 100.0),
            frame_segment_index=1,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
        )

        # Vertical rod
        rod_angle = 0.0

        start_cut, end_cut = generator._calculate_cut_angles(
            rod_angle_deg=rod_angle,
            start_anchor=start_anchor,
            end_anchor=end_anchor,
        )

        # Start: 0° - 90° = -90°
        # End: 0° - 0° = 0°
        assert start_cut == -90.0
        assert end_cut == 0.0

    def test_calculate_cut_angles_extreme_case_2(self) -> None:
        """Test normalization with large positive difference."""
        generator = RandomGeneratorV2()

        start_anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=False,
            frame_segment_angle_deg=-85.0,
        )

        end_anchor = AnchorPoint(
            position=(0.0, 100.0),
            frame_segment_index=1,
            is_vertical_segment=False,
            frame_segment_angle_deg=85.0,
        )

        # Rod at 45°
        rod_angle = 45.0

        start_cut, end_cut = generator._calculate_cut_angles(
            rod_angle_deg=rod_angle,
            start_anchor=start_anchor,
            end_anchor=end_anchor,
        )

        # Start: 45° - (-85°) = 130° -> normalized to 50° (180 - 130)
        # End: 45° - 85° = -40°
        assert abs(start_cut - 50.0) < 0.1
        assert end_cut == -40.0


class TestRodCreationWithCutAngles:
    """Test that rods are created with correct cut angles."""

    def test_rod_has_cut_angles_from_calculation(self) -> None:
        """Test that Rod objects store the calculated cut angles."""
        rod = Rod(
            geometry=LineString([(0.0, 0.0), (10.0, 100.0)]),
            start_cut_angle_deg=15.0,
            end_cut_angle_deg=-10.0,
            weight_kg_m=0.5,
            layer=1,
        )

        assert rod.start_cut_angle_deg == 15.0
        assert rod.end_cut_angle_deg == -10.0
