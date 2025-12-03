"""Property-based tests for ParallelogramRailingShape.

Uses Hypothesis for property-based testing to verify correctness properties
defined in the design document.
"""

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from railing_generator.domain.shapes.parallelogram_railing_shape import (
    ParallelogramRailingShape,
    ParallelogramRailingShapeParameters,
)


# Strategy for generating valid positive floats within reasonable bounds
positive_float = st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False)

# Strategy for generating valid parallelogram parameters
valid_params_strategy = st.builds(
    ParallelogramRailingShapeParameters,
    post_length_cm=positive_float,
    slope_width_cm=positive_float,
    slope_height_cm=positive_float,
    frame_weight_per_meter_kg_m=positive_float,
)


class TestParameterValidation:
    """Property tests for parameter validation."""

    @settings(max_examples=100)
    @given(
        post_length_cm=positive_float,
        slope_width_cm=positive_float,
        slope_height_cm=positive_float,
        frame_weight_per_meter_kg_m=positive_float,
    )
    def test_positive_parameters_accepted(
        self,
        post_length_cm: float,
        slope_width_cm: float,
        slope_height_cm: float,
        frame_weight_per_meter_kg_m: float,
    ) -> None:
        """
        **Feature: parallelogram-railing-shape, Property 6: Positive Parameters Accepted**

        *For any* set of positive values for post_length_cm, slope_width_cm,
        slope_height_cm, and frame_weight_per_meter_kg_m, creating
        ParallelogramRailingShapeParameters SHALL succeed without validation errors.

        **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
        """
        # Should not raise any exception
        params = ParallelogramRailingShapeParameters(
            post_length_cm=post_length_cm,
            slope_width_cm=slope_width_cm,
            slope_height_cm=slope_height_cm,
            frame_weight_per_meter_kg_m=frame_weight_per_meter_kg_m,
        )

        # Verify values are stored correctly
        assert params.post_length_cm == post_length_cm
        assert params.slope_width_cm == slope_width_cm
        assert params.slope_height_cm == slope_height_cm
        assert params.frame_weight_per_meter_kg_m == frame_weight_per_meter_kg_m

    @settings(max_examples=100)
    @given(
        invalid_value=st.floats(max_value=0.0, allow_nan=False, allow_infinity=False),
        field_index=st.integers(min_value=0, max_value=3),
    )
    def test_invalid_parameters_rejected(self, invalid_value: float, field_index: int) -> None:
        """
        **Feature: parallelogram-railing-shape, Property 7: Invalid Parameters Rejected**

        *For any* parameter value that is zero or negative, creating
        ParallelogramRailingShapeParameters SHALL raise a validation error.

        **Validates: Requirements 2.5**
        """
        # Base valid values
        values = {
            "post_length_cm": 100.0,
            "slope_width_cm": 300.0,
            "slope_height_cm": 150.0,
            "frame_weight_per_meter_kg_m": 0.5,
        }

        # Replace one field with invalid value
        field_names = list(values.keys())
        values[field_names[field_index]] = invalid_value

        with pytest.raises(ValidationError):
            ParallelogramRailingShapeParameters(**values)

    @settings(max_examples=100)
    @given(params=valid_params_strategy)
    def test_serialization_round_trip(self, params: ParallelogramRailingShapeParameters) -> None:
        """
        **Feature: parallelogram-railing-shape, Property 8: Serialization Round-Trip**

        *For any* valid ParallelogramRailingShapeParameters, serializing to JSON
        and deserializing back SHALL produce parameters equal to the original.

        **Validates: Requirements 4.1, 4.2**
        """
        # Serialize to JSON
        json_str = params.model_dump_json()

        # Deserialize back
        restored = ParallelogramRailingShapeParameters.model_validate_json(json_str)

        # Verify equality
        assert restored.type == params.type
        assert restored.post_length_cm == params.post_length_cm
        assert restored.slope_width_cm == params.slope_width_cm
        assert restored.slope_height_cm == params.slope_height_cm
        assert restored.frame_weight_per_meter_kg_m == params.frame_weight_per_meter_kg_m


class TestFrameGeometry:
    """Property tests for frame geometry generation."""

    @settings(max_examples=100)
    @given(params=valid_params_strategy)
    def test_frame_rod_count(self, params: ParallelogramRailingShapeParameters) -> None:
        """
        **Feature: parallelogram-railing-shape, Property 1: Frame Rod Count**

        *For any* valid ParallelogramRailingShapeParameters, generating a frame
        SHALL produce exactly 4 rods.

        **Validates: Requirements 1.1**
        """
        shape = ParallelogramRailingShape(params)
        frame = shape.generate_frame()

        assert len(frame.rods) == 4

    @settings(max_examples=100)
    @given(params=valid_params_strategy)
    def test_handrail_and_bottom_rail_parallelism(
        self, params: ParallelogramRailingShapeParameters
    ) -> None:
        """
        **Feature: parallelogram-railing-shape, Property 2: Handrail and Bottom Rail Parallelism**

        *For any* valid ParallelogramRailingShapeParameters, the handrail and
        bottom rail SHALL have identical slopes (be parallel).

        **Validates: Requirements 1.2**
        """
        shape = ParallelogramRailingShape(params)
        frame = shape.generate_frame()

        # Rod order: left_post, handrail, right_post, bottom_rail
        handrail = frame.rods[1]
        bottom_rail = frame.rods[3]

        # Get coordinates
        handrail_coords = list(handrail.geometry.coords)
        bottom_rail_coords = list(bottom_rail.geometry.coords)

        # Calculate slopes (dy/dx)
        handrail_dx = handrail_coords[1][0] - handrail_coords[0][0]
        handrail_dy = handrail_coords[1][1] - handrail_coords[0][1]

        bottom_rail_dx = bottom_rail_coords[1][0] - bottom_rail_coords[0][0]
        bottom_rail_dy = bottom_rail_coords[1][1] - bottom_rail_coords[0][1]

        # For parallel lines, the slopes should be equal
        # Using cross product: if parallel, dx1*dy2 - dy1*dx2 = 0
        cross_product = handrail_dx * bottom_rail_dy - handrail_dy * bottom_rail_dx

        # Use relative tolerance for large values to handle floating point precision
        max_magnitude = max(
            abs(handrail_dx * bottom_rail_dy),
            abs(handrail_dy * bottom_rail_dx),
            1.0,  # Minimum to avoid division issues
        )
        assert abs(cross_product) < max_magnitude * 1e-9

    @settings(max_examples=100)
    @given(params=valid_params_strategy)
    def test_posts_are_vertical(self, params: ParallelogramRailingShapeParameters) -> None:
        """
        **Feature: parallelogram-railing-shape, Property 3: Posts Are Vertical**

        *For any* valid ParallelogramRailingShapeParameters, both the left and
        right posts SHALL be vertical (start and end x-coordinates are equal).

        **Validates: Requirements 1.3**
        """
        shape = ParallelogramRailingShape(params)
        frame = shape.generate_frame()

        # Rod order: left_post, handrail, right_post, bottom_rail
        left_post = frame.rods[0]
        right_post = frame.rods[2]

        # Get coordinates
        left_post_coords = list(left_post.geometry.coords)
        right_post_coords = list(right_post.geometry.coords)

        # Verify left post is vertical (same x at start and end)
        assert math.isclose(left_post_coords[0][0], left_post_coords[1][0], abs_tol=1e-9)

        # Verify right post is vertical (same x at start and end)
        assert math.isclose(right_post_coords[0][0], right_post_coords[1][0], abs_tol=1e-9)

    @settings(max_examples=100)
    @given(params=valid_params_strategy)
    def test_left_post_position(self, params: ParallelogramRailingShapeParameters) -> None:
        """
        **Feature: parallelogram-railing-shape, Property 4: Left Post Position**

        *For any* valid ParallelogramRailingShapeParameters, the left post SHALL
        start at (0, 0) and end at (0, post_length_cm).

        **Validates: Requirements 1.4**
        """
        shape = ParallelogramRailingShape(params)
        frame = shape.generate_frame()

        # Rod order: left_post, handrail, right_post, bottom_rail
        left_post = frame.rods[0]
        coords = list(left_post.geometry.coords)

        # Verify start at origin
        assert math.isclose(coords[0][0], 0.0, abs_tol=1e-9)
        assert math.isclose(coords[0][1], 0.0, abs_tol=1e-9)

        # Verify end at (0, post_length_cm)
        assert math.isclose(coords[1][0], 0.0, abs_tol=1e-9)
        assert math.isclose(coords[1][1], params.post_length_cm, abs_tol=1e-9)

    @settings(max_examples=100)
    @given(params=valid_params_strategy)
    def test_right_post_base_position(self, params: ParallelogramRailingShapeParameters) -> None:
        """
        **Feature: parallelogram-railing-shape, Property 5: Right Post Base Position**

        *For any* valid ParallelogramRailingShapeParameters, the right post base
        SHALL be at (slope_width_cm, slope_height_cm).

        **Validates: Requirements 1.5**
        """
        shape = ParallelogramRailingShape(params)
        frame = shape.generate_frame()

        # Rod order: left_post, handrail, right_post, bottom_rail
        right_post = frame.rods[2]
        coords = list(right_post.geometry.coords)

        # Right post goes from top to bottom, so base is at coords[1]
        assert math.isclose(coords[1][0], params.slope_width_cm, abs_tol=1e-9)
        assert math.isclose(coords[1][1], params.slope_height_cm, abs_tol=1e-9)
