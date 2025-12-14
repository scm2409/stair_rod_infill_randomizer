"""Property-based tests for UniformDirectionalGeneratorParameters.

Uses Hypothesis for property-based testing to verify correctness properties
defined in the design document.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from railing_generator.domain.infill_generators.uniform_directional_generator_parameters import (
    UniformDirectionalGeneratorParameters,
)


# Strategy for generating valid direction ranges where min < max
@st.composite
def valid_direction_range(draw: st.DrawFn) -> tuple[float, float]:
    """Generate a valid direction range where min < max."""
    min_deg = draw(
        st.floats(min_value=-90.0, max_value=89.0, allow_nan=False, allow_infinity=False)
    )
    # Ensure max is strictly greater than min
    max_deg = draw(
        st.floats(min_value=min_deg + 0.1, max_value=90.0, allow_nan=False, allow_infinity=False)
    )
    return (min_deg, max_deg)


# Strategy for generating invalid direction ranges where min >= max
@st.composite
def invalid_direction_range(draw: st.DrawFn) -> tuple[float, float]:
    """Generate an invalid direction range where min >= max."""
    min_deg = draw(
        st.floats(min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False)
    )
    # max_deg is less than or equal to min_deg
    max_deg = draw(
        st.floats(min_value=-90.0, max_value=min_deg, allow_nan=False, allow_infinity=False)
    )
    return (min_deg, max_deg)


# Strategy for generating valid positive integers for num_rods
valid_num_rods = st.integers(min_value=1, max_value=200)

# Strategy for generating valid positive integers for num_layers
valid_num_layers = st.integers(min_value=1, max_value=10)

# Strategy for generating valid positive floats for min_anchor_distance_cm
valid_min_anchor_distance_cm = st.floats(
    min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False
)

# Strategy for generating valid positive floats for infill_weight_per_meter_kg_m
valid_infill_weight = st.floats(
    min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False
)


class TestParameterValidationProperty:
    """
    **Feature: uniform-directional-generator, Property 7: Parameter Validation**

    *For any* parameter values where direction range min >= max, or any value
    is outside its valid range, parameter creation SHALL raise a validation error.

    **Validates: Requirements 2.6, 2.7**
    """

    @settings(max_examples=100)
    @given(
        num_rods=valid_num_rods,
        num_layers=valid_num_layers,
        direction_range=valid_direction_range(),
        min_anchor_distance_cm=valid_min_anchor_distance_cm,
        infill_weight_per_meter_kg_m=valid_infill_weight,
    )
    def test_valid_parameters_accepted(
        self,
        num_rods: int,
        num_layers: int,
        direction_range: tuple[float, float],
        min_anchor_distance_cm: float,
        infill_weight_per_meter_kg_m: float,
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 7: Parameter Validation**

        *For any* valid parameter values (positive num_rods, positive num_layers,
        direction range where min < max, positive min_anchor_distance_cm,
        positive infill_weight_per_meter_kg_m), creating
        UniformDirectionalGeneratorParameters SHALL succeed without validation errors.

        **Validates: Requirements 2.6, 2.7**
        """
        min_deg, max_deg = direction_range

        # Should not raise any exception
        params = UniformDirectionalGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=infill_weight_per_meter_kg_m,
        )

        # Verify values are stored correctly
        assert params.num_rods == num_rods
        assert params.num_layers == num_layers
        assert params.main_direction_range_min_deg == min_deg
        assert params.main_direction_range_max_deg == max_deg
        assert params.min_anchor_distance_cm == min_anchor_distance_cm
        assert params.infill_weight_per_meter_kg_m == infill_weight_per_meter_kg_m

    @settings(max_examples=100)
    @given(direction_range=invalid_direction_range())
    def test_invalid_direction_range_rejected(
        self,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: uniform-directional-generator, Property 7: Parameter Validation**

        *For any* direction range where min >= max, creating
        UniformDirectionalGeneratorParameters SHALL raise a validation error.

        **Validates: Requirements 2.6, 2.7**
        """
        min_deg, max_deg = direction_range

        with pytest.raises(ValidationError):
            UniformDirectionalGeneratorParameters(
                num_rods=30,
                num_layers=3,
                main_direction_range_min_deg=min_deg,
                main_direction_range_max_deg=max_deg,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=0.59,
            )

    @settings(max_examples=100)
    @given(
        invalid_num_rods=st.integers(max_value=0),
    )
    def test_invalid_num_rods_rejected(self, invalid_num_rods: int) -> None:
        """
        **Feature: uniform-directional-generator, Property 7: Parameter Validation**

        *For any* num_rods <= 0, creating UniformDirectionalGeneratorParameters
        SHALL raise a validation error.

        **Validates: Requirements 2.6, 2.7**
        """
        with pytest.raises(ValidationError):
            UniformDirectionalGeneratorParameters(
                num_rods=invalid_num_rods,
                num_layers=3,
                main_direction_range_min_deg=-45.0,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=0.59,
            )

    @settings(max_examples=100)
    @given(
        invalid_num_layers=st.integers(max_value=0),
    )
    def test_invalid_num_layers_rejected(self, invalid_num_layers: int) -> None:
        """
        **Feature: uniform-directional-generator, Property 7: Parameter Validation**

        *For any* num_layers <= 0, creating UniformDirectionalGeneratorParameters
        SHALL raise a validation error.

        **Validates: Requirements 2.6, 2.7**
        """
        with pytest.raises(ValidationError):
            UniformDirectionalGeneratorParameters(
                num_rods=30,
                num_layers=invalid_num_layers,
                main_direction_range_min_deg=-45.0,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=0.59,
            )

    @settings(max_examples=100)
    @given(
        invalid_min_anchor_distance=st.floats(max_value=0.0, allow_nan=False, allow_infinity=False),
    )
    def test_invalid_min_anchor_distance_rejected(self, invalid_min_anchor_distance: float) -> None:
        """
        **Feature: uniform-directional-generator, Property 7: Parameter Validation**

        *For any* min_anchor_distance_cm <= 0, creating
        UniformDirectionalGeneratorParameters SHALL raise a validation error.

        **Validates: Requirements 2.6, 2.7**
        """
        with pytest.raises(ValidationError):
            UniformDirectionalGeneratorParameters(
                num_rods=30,
                num_layers=3,
                main_direction_range_min_deg=-45.0,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=invalid_min_anchor_distance,
                infill_weight_per_meter_kg_m=0.59,
            )

    @settings(max_examples=100)
    @given(
        invalid_weight=st.floats(max_value=0.0, allow_nan=False, allow_infinity=False),
    )
    def test_invalid_infill_weight_rejected(self, invalid_weight: float) -> None:
        """
        **Feature: uniform-directional-generator, Property 7: Parameter Validation**

        *For any* infill_weight_per_meter_kg_m <= 0, creating
        UniformDirectionalGeneratorParameters SHALL raise a validation error.

        **Validates: Requirements 2.6, 2.7**
        """
        with pytest.raises(ValidationError):
            UniformDirectionalGeneratorParameters(
                num_rods=30,
                num_layers=3,
                main_direction_range_min_deg=-45.0,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=invalid_weight,
            )

    @settings(max_examples=100)
    @given(
        min_deg=st.floats(min_value=-200.0, max_value=-90.1, allow_nan=False, allow_infinity=False)
        | st.floats(min_value=90.1, max_value=200.0, allow_nan=False, allow_infinity=False),
    )
    def test_direction_out_of_range_rejected(self, min_deg: float) -> None:
        """
        **Feature: uniform-directional-generator, Property 7: Parameter Validation**

        *For any* direction angle outside [-90, 90], creating
        UniformDirectionalGeneratorParameters SHALL raise a validation error.

        **Validates: Requirements 2.6, 2.7**
        """
        with pytest.raises(ValidationError):
            UniformDirectionalGeneratorParameters(
                num_rods=30,
                num_layers=3,
                main_direction_range_min_deg=min_deg,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=0.59,
            )
