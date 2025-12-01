"""Tests for anchor point margin constraints from frame rod ends."""

import pytest
from shapely.geometry import LineString

from railing_generator.domain.infill_generators.random_generator_v2 import RandomGeneratorV2
from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
    RandomGeneratorParametersV2,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.rod import Rod
from railing_generator.domain.shapes.rectangular_railing_shape import (
    RectangularRailingShape,
    RectangularRailingShapeParameters,
)


class TestAnchorPointMargins:
    """Test that anchor points maintain minimum distance from frame rod ends."""

    def test_anchor_points_have_minimum_margin_from_segment_ends(self) -> None:
        """Test that all anchor points are at least 2cm from segment start/end."""
        # Create a rectangular frame
        params = RectangularRailingShapeParameters(
            width_cm=100.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )
        shape = RectangularRailingShape(params)
        frame = shape.generate_frame()

        # Create generator and parameters
        generator = RandomGeneratorV2()
        from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
            RandomGeneratorDefaultsV2,
        )

        defaults = RandomGeneratorDefaultsV2()
        gen_params = RandomGeneratorParametersV2.from_defaults(defaults)
        gen_params = RandomGeneratorParametersV2(
            **{
                **gen_params.model_dump(),
                "num_rods": 10,
                "num_layers": 2,
                "min_anchor_distance_vertical_cm": 10.0,
                "min_anchor_distance_other_cm": 10.0,
            }
        )

        # Generate anchor points
        anchor_points_by_segment = generator._generate_anchor_points_by_frame_segment(
            frame, gen_params
        )

        # Check each segment
        min_margin_cm = 2.0
        for segment_idx, anchors in anchor_points_by_segment.items():
            frame_rod = frame.rods[segment_idx]
            segment_length = frame_rod.geometry.length

            for anchor in anchors:
                # Calculate distance along the segment for this anchor
                # Use shapely's project method to get distance along line
                # anchor.position is already a Shapely Point
                distance_along_segment = frame_rod.geometry.project(anchor.position)

                # Check that anchor is at least min_margin_cm from both ends
                assert distance_along_segment >= min_margin_cm - 0.1, (
                    f"Anchor at segment {segment_idx} is too close to start: "
                    f"{distance_along_segment:.2f}cm < {min_margin_cm}cm"
                )

                distance_from_end = segment_length - distance_along_segment
                assert distance_from_end >= min_margin_cm - 0.1, (
                    f"Anchor at segment {segment_idx} is too close to end: "
                    f"{distance_from_end:.2f}cm < {min_margin_cm}cm"
                )

    def test_short_segments_skip_anchor_generation(self) -> None:
        """Test that very short segments (< 4cm) skip anchor generation."""
        # Create a frame with a very short rod
        short_rod = Rod(
            geometry=LineString([(0, 0), (3, 0)]),  # 3cm long
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        )

        normal_rod = Rod(
            geometry=LineString([(3, 0), (3, 100)]),  # 100cm long
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        )

        frame = RailingFrame(rods=[short_rod, normal_rod])

        # Create generator and parameters
        generator = RandomGeneratorV2()
        from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
            RandomGeneratorDefaultsV2,
        )

        defaults = RandomGeneratorDefaultsV2()
        gen_params = RandomGeneratorParametersV2.from_defaults(defaults)
        gen_params = RandomGeneratorParametersV2(
            **{
                **gen_params.model_dump(),
                "num_rods": 5,
                "num_layers": 1,
                "min_anchor_distance_vertical_cm": 10.0,
                "min_anchor_distance_other_cm": 10.0,
            }
        )

        # Generate anchor points
        anchor_points_by_segment = generator._generate_anchor_points_by_frame_segment(
            frame, gen_params
        )

        # Short segment should have no anchors
        assert len(anchor_points_by_segment[0]) == 0, (
            "Short segment should not have any anchor points"
        )

        # Normal segment should have anchors
        assert len(anchor_points_by_segment[1]) > 0, "Normal segment should have anchor points"

    def test_single_anchor_placed_in_middle_of_usable_range(self) -> None:
        """Test that when only one anchor fits, it's placed in the middle."""
        # Create a frame with a rod that can only fit one anchor
        rod = Rod(
            geometry=LineString([(0, 0), (15, 0)]),  # 15cm long
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        )

        frame = RailingFrame(rods=[rod])

        # Create generator and parameters
        generator = RandomGeneratorV2()
        from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
            RandomGeneratorDefaultsV2,
        )

        defaults = RandomGeneratorDefaultsV2()
        gen_params = RandomGeneratorParametersV2.from_defaults(defaults)
        gen_params = RandomGeneratorParametersV2(
            **{
                **gen_params.model_dump(),
                "num_rods": 5,
                "num_layers": 1,
                "min_anchor_distance_vertical_cm": 20.0,  # Large spacing
                "min_anchor_distance_other_cm": 20.0,
            }
        )

        # Generate anchor points
        anchor_points_by_segment = generator._generate_anchor_points_by_frame_segment(
            frame, gen_params
        )

        # Should have exactly one anchor
        anchors = anchor_points_by_segment[0]
        assert len(anchors) == 1, "Should have exactly one anchor"

        # Check that it's roughly in the middle (allowing for random offset)
        from shapely.geometry import Point

        anchor_shapely = Point(anchors[0].position)
        distance_along = rod.geometry.project(anchor_shapely)

        # Should be roughly in the middle of the 15cm rod (around 7.5cm)
        # With 2cm margins, usable range is 2-13cm, middle is 7.5cm
        expected_middle = 7.5
        assert abs(distance_along - expected_middle) < 2.0, (
            f"Single anchor should be near middle: {distance_along:.2f}cm vs {expected_middle:.2f}cm"
        )
