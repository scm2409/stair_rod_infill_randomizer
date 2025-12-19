"""Property-based tests for EvolutionaryInfillGeneratorParameters.

Uses Hypothesis for property-based testing to verify correctness properties
defined in the design document.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from railing_generator.domain.infill_generators.evolutionary_infill_generator_parameters import (
    EvolutionaryInfillGeneratorDefaults,
    EvolutionaryInfillGeneratorParameters,
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


# Strategies for valid baseline parameters
valid_num_rods = st.integers(min_value=1, max_value=200)
valid_num_layers = st.integers(min_value=1, max_value=10)
valid_min_anchor_distance_cm = st.floats(
    min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False
)
valid_infill_weight = st.floats(
    min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False
)

# Strategies for valid evolutionary parameters
valid_max_iterations = st.integers(min_value=1, max_value=100000)
valid_max_duration_sec = st.floats(
    min_value=0.1, max_value=3600.0, allow_nan=False, allow_infinity=False
)
valid_improvement_threshold = st.floats(
    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
)
valid_stagnation_limit = st.integers(min_value=1, max_value=10000)
valid_max_direction_deviation_deg = st.floats(
    min_value=0.0, max_value=90.0, allow_nan=False, allow_infinity=False
)


# Strategy for generating valid EvolutionaryInfillGeneratorParameters
@st.composite
def valid_evolutionary_params(draw: st.DrawFn) -> EvolutionaryInfillGeneratorParameters:
    """Generate valid EvolutionaryInfillGeneratorParameters."""
    direction_range = draw(valid_direction_range())
    return EvolutionaryInfillGeneratorParameters(
        num_rods=draw(valid_num_rods),
        num_layers=draw(valid_num_layers),
        main_direction_range_min_deg=direction_range[0],
        main_direction_range_max_deg=direction_range[1],
        min_anchor_distance_cm=draw(valid_min_anchor_distance_cm),
        infill_weight_per_meter_kg_m=draw(valid_infill_weight),
        max_iterations=draw(valid_max_iterations),
        max_duration_sec=draw(valid_max_duration_sec),
        improvement_threshold=draw(valid_improvement_threshold),
        stagnation_limit=draw(valid_stagnation_limit),
        max_direction_deviation_deg=draw(valid_max_direction_deviation_deg),
    )


class TestParameterValidationProperty:
    """
    **Feature: evolutionary-infill-generator, Property 9: Parameter Validation**

    *For any* parameter values where direction range min >= max, or any value
    is outside its valid range, parameter creation SHALL raise a validation error.

    **Validates: Requirements 8.3, 9.1-9.6**
    """

    @settings(max_examples=20)
    @given(
        num_rods=valid_num_rods,
        num_layers=valid_num_layers,
        direction_range=valid_direction_range(),
        min_anchor_distance_cm=valid_min_anchor_distance_cm,
        infill_weight_per_meter_kg_m=valid_infill_weight,
        max_iterations=valid_max_iterations,
        max_duration_sec=valid_max_duration_sec,
        improvement_threshold=valid_improvement_threshold,
        stagnation_limit=valid_stagnation_limit,
        max_direction_deviation_deg=valid_max_direction_deviation_deg,
    )
    def test_valid_parameters_accepted(
        self,
        num_rods: int,
        num_layers: int,
        direction_range: tuple[float, float],
        min_anchor_distance_cm: float,
        infill_weight_per_meter_kg_m: float,
        max_iterations: int,
        max_duration_sec: float,
        improvement_threshold: float,
        stagnation_limit: int,
        max_direction_deviation_deg: float,
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 9: Parameter Validation**

        *For any* valid parameter values, creating EvolutionaryInfillGeneratorParameters
        SHALL succeed without validation errors.

        **Validates: Requirements 8.3, 9.1-9.6**
        """
        min_deg, max_deg = direction_range

        # Should not raise any exception
        params = EvolutionaryInfillGeneratorParameters(
            num_rods=num_rods,
            num_layers=num_layers,
            main_direction_range_min_deg=min_deg,
            main_direction_range_max_deg=max_deg,
            min_anchor_distance_cm=min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=infill_weight_per_meter_kg_m,
            max_iterations=max_iterations,
            max_duration_sec=max_duration_sec,
            improvement_threshold=improvement_threshold,
            stagnation_limit=stagnation_limit,
            max_direction_deviation_deg=max_direction_deviation_deg,
        )

        # Verify baseline values are stored correctly
        assert params.num_rods == num_rods
        assert params.num_layers == num_layers
        assert params.main_direction_range_min_deg == min_deg
        assert params.main_direction_range_max_deg == max_deg
        assert params.min_anchor_distance_cm == min_anchor_distance_cm
        assert params.infill_weight_per_meter_kg_m == infill_weight_per_meter_kg_m

        # Verify evolutionary values are stored correctly
        assert params.max_iterations == max_iterations
        assert params.max_duration_sec == max_duration_sec
        assert params.improvement_threshold == improvement_threshold
        assert params.stagnation_limit == stagnation_limit
        assert params.max_direction_deviation_deg == max_direction_deviation_deg

        # Verify type discriminator
        assert params.type == "evolutionary"

    @settings(max_examples=20)
    @given(direction_range=invalid_direction_range())
    def test_invalid_direction_range_rejected(
        self,
        direction_range: tuple[float, float],
    ) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 9: Parameter Validation**

        *For any* direction range where min >= max, creating
        EvolutionaryInfillGeneratorParameters SHALL raise a validation error.

        **Validates: Requirements 8.3, 9.1-9.6**
        """
        min_deg, max_deg = direction_range

        with pytest.raises(ValidationError):
            EvolutionaryInfillGeneratorParameters(
                num_rods=30,
                num_layers=3,
                main_direction_range_min_deg=min_deg,
                main_direction_range_max_deg=max_deg,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=0.59,
                max_iterations=1000,
                max_duration_sec=60.0,
                improvement_threshold=0.001,
                stagnation_limit=100,
                max_direction_deviation_deg=90.0,
            )

    @settings(max_examples=20)
    @given(invalid_num_rods=st.integers(max_value=0))
    def test_invalid_num_rods_rejected(self, invalid_num_rods: int) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 9: Parameter Validation**

        *For any* num_rods <= 0, creating EvolutionaryInfillGeneratorParameters
        SHALL raise a validation error.

        **Validates: Requirements 8.3, 9.1-9.6**
        """
        with pytest.raises(ValidationError):
            EvolutionaryInfillGeneratorParameters(
                num_rods=invalid_num_rods,
                num_layers=3,
                main_direction_range_min_deg=-45.0,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=0.59,
                max_iterations=1000,
                max_duration_sec=60.0,
                improvement_threshold=0.001,
                stagnation_limit=100,
                max_direction_deviation_deg=90.0,
            )

    @settings(max_examples=20)
    @given(invalid_num_layers=st.integers(max_value=0))
    def test_invalid_num_layers_rejected(self, invalid_num_layers: int) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 9: Parameter Validation**

        *For any* num_layers <= 0, creating EvolutionaryInfillGeneratorParameters
        SHALL raise a validation error.

        **Validates: Requirements 8.3, 9.1-9.6**
        """
        with pytest.raises(ValidationError):
            EvolutionaryInfillGeneratorParameters(
                num_rods=30,
                num_layers=invalid_num_layers,
                main_direction_range_min_deg=-45.0,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=0.59,
                max_iterations=1000,
                max_duration_sec=60.0,
                improvement_threshold=0.001,
                stagnation_limit=100,
                max_direction_deviation_deg=90.0,
            )

    @settings(max_examples=20)
    @given(
        invalid_min_anchor_distance=st.floats(max_value=0.0, allow_nan=False, allow_infinity=False)
    )
    def test_invalid_min_anchor_distance_rejected(self, invalid_min_anchor_distance: float) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 9: Parameter Validation**

        *For any* min_anchor_distance_cm <= 0, creating
        EvolutionaryInfillGeneratorParameters SHALL raise a validation error.

        **Validates: Requirements 8.3, 9.1-9.6**
        """
        with pytest.raises(ValidationError):
            EvolutionaryInfillGeneratorParameters(
                num_rods=30,
                num_layers=3,
                main_direction_range_min_deg=-45.0,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=invalid_min_anchor_distance,
                infill_weight_per_meter_kg_m=0.59,
                max_iterations=1000,
                max_duration_sec=60.0,
                improvement_threshold=0.001,
                stagnation_limit=100,
                max_direction_deviation_deg=90.0,
            )

    @settings(max_examples=20)
    @given(invalid_weight=st.floats(max_value=0.0, allow_nan=False, allow_infinity=False))
    def test_invalid_infill_weight_rejected(self, invalid_weight: float) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 9: Parameter Validation**

        *For any* infill_weight_per_meter_kg_m <= 0, creating
        EvolutionaryInfillGeneratorParameters SHALL raise a validation error.

        **Validates: Requirements 8.3, 9.1-9.6**
        """
        with pytest.raises(ValidationError):
            EvolutionaryInfillGeneratorParameters(
                num_rods=30,
                num_layers=3,
                main_direction_range_min_deg=-45.0,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=invalid_weight,
                max_iterations=1000,
                max_duration_sec=60.0,
                improvement_threshold=0.001,
                stagnation_limit=100,
                max_direction_deviation_deg=90.0,
            )

    @settings(max_examples=20)
    @given(invalid_max_iterations=st.integers(max_value=0))
    def test_invalid_max_iterations_rejected(self, invalid_max_iterations: int) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 9: Parameter Validation**

        *For any* max_iterations <= 0, creating EvolutionaryInfillGeneratorParameters
        SHALL raise a validation error.

        **Validates: Requirements 8.3, 9.1-9.6**
        """
        with pytest.raises(ValidationError):
            EvolutionaryInfillGeneratorParameters(
                num_rods=30,
                num_layers=3,
                main_direction_range_min_deg=-45.0,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=0.59,
                max_iterations=invalid_max_iterations,
                max_duration_sec=60.0,
                improvement_threshold=0.001,
                stagnation_limit=100,
                max_direction_deviation_deg=90.0,
            )

    @settings(max_examples=20)
    @given(invalid_max_duration=st.floats(max_value=0.0, allow_nan=False, allow_infinity=False))
    def test_invalid_max_duration_rejected(self, invalid_max_duration: float) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 9: Parameter Validation**

        *For any* max_duration_sec <= 0, creating EvolutionaryInfillGeneratorParameters
        SHALL raise a validation error.

        **Validates: Requirements 8.3, 9.1-9.6**
        """
        with pytest.raises(ValidationError):
            EvolutionaryInfillGeneratorParameters(
                num_rods=30,
                num_layers=3,
                main_direction_range_min_deg=-45.0,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=0.59,
                max_iterations=1000,
                max_duration_sec=invalid_max_duration,
                improvement_threshold=0.001,
                stagnation_limit=100,
                max_direction_deviation_deg=90.0,
            )

    @settings(max_examples=20)
    @given(invalid_stagnation_limit=st.integers(max_value=0))
    def test_invalid_stagnation_limit_rejected(self, invalid_stagnation_limit: int) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 9: Parameter Validation**

        *For any* stagnation_limit <= 0, creating EvolutionaryInfillGeneratorParameters
        SHALL raise a validation error.

        **Validates: Requirements 8.3, 9.1-9.6**
        """
        with pytest.raises(ValidationError):
            EvolutionaryInfillGeneratorParameters(
                num_rods=30,
                num_layers=3,
                main_direction_range_min_deg=-45.0,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=0.59,
                max_iterations=1000,
                max_duration_sec=60.0,
                improvement_threshold=0.001,
                stagnation_limit=invalid_stagnation_limit,
                max_direction_deviation_deg=90.0,
            )

    @settings(max_examples=20)
    @given(
        invalid_threshold=st.floats(min_value=1.01, max_value=10.0, allow_nan=False)
        | st.floats(max_value=-0.01, allow_nan=False, allow_infinity=False)
    )
    def test_invalid_improvement_threshold_rejected(self, invalid_threshold: float) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 9: Parameter Validation**

        *For any* improvement_threshold outside [0, 1], creating
        EvolutionaryInfillGeneratorParameters SHALL raise a validation error.

        **Validates: Requirements 8.3, 9.1-9.6**
        """
        with pytest.raises(ValidationError):
            EvolutionaryInfillGeneratorParameters(
                num_rods=30,
                num_layers=3,
                main_direction_range_min_deg=-45.0,
                main_direction_range_max_deg=25.0,
                min_anchor_distance_cm=5.0,
                infill_weight_per_meter_kg_m=0.59,
                max_iterations=1000,
                max_duration_sec=60.0,
                improvement_threshold=invalid_threshold,
                stagnation_limit=100,
                max_direction_deviation_deg=90.0,
            )


class TestFromDefaultsMethod:
    """Tests for the from_defaults class method."""

    def test_from_defaults_creates_valid_parameters(self) -> None:
        """Test that from_defaults creates valid parameters from defaults."""
        defaults = EvolutionaryInfillGeneratorDefaults()
        params = EvolutionaryInfillGeneratorParameters.from_defaults(defaults)

        # Verify baseline parameters
        assert params.num_rods == defaults.num_rods
        assert params.num_layers == defaults.num_layers
        assert params.main_direction_range_min_deg == defaults.main_direction_range_min_deg
        assert params.main_direction_range_max_deg == defaults.main_direction_range_max_deg
        assert params.min_anchor_distance_cm == defaults.min_anchor_distance_cm
        assert params.infill_weight_per_meter_kg_m == defaults.infill_weight_per_meter_kg_m

        # Verify evolutionary parameters
        assert params.max_iterations == defaults.max_iterations
        assert params.max_duration_sec == defaults.max_duration_sec
        assert params.improvement_threshold == defaults.improvement_threshold
        assert params.stagnation_limit == defaults.stagnation_limit
        assert params.max_direction_deviation_deg == defaults.max_direction_deviation_deg

        # Verify type discriminator
        assert params.type == "evolutionary"

        # Verify default evaluator
        assert params.evaluator.type == "passthrough"


class TestSerializationRoundTripProperty:
    """
    **Feature: evolutionary-infill-generator, Property 10: Serialization Round-Trip**

    *For any* valid EvolutionaryInfillGeneratorParameters, serializing to JSON
    and deserializing SHALL produce an equivalent object.

    **Validates: Requirements 12.1, 12.2**
    """

    @settings(max_examples=20)
    @given(params=valid_evolutionary_params())
    def test_json_round_trip(self, params: EvolutionaryInfillGeneratorParameters) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 10: Serialization Round-Trip**

        *For any* valid EvolutionaryInfillGeneratorParameters, serializing to JSON
        and deserializing back SHALL produce parameters equal to the original.

        **Validates: Requirements 12.1, 12.2**
        """
        # Serialize to JSON
        json_str = params.model_dump_json()

        # Deserialize from JSON
        restored = EvolutionaryInfillGeneratorParameters.model_validate_json(json_str)

        # Verify all baseline parameters match
        assert restored.num_rods == params.num_rods
        assert restored.num_layers == params.num_layers
        assert restored.main_direction_range_min_deg == params.main_direction_range_min_deg
        assert restored.main_direction_range_max_deg == params.main_direction_range_max_deg
        assert restored.min_anchor_distance_cm == params.min_anchor_distance_cm
        assert restored.infill_weight_per_meter_kg_m == params.infill_weight_per_meter_kg_m

        # Verify all evolutionary parameters match
        assert restored.max_iterations == params.max_iterations
        assert restored.max_duration_sec == params.max_duration_sec
        assert restored.improvement_threshold == params.improvement_threshold
        assert restored.stagnation_limit == params.stagnation_limit
        assert restored.max_direction_deviation_deg == params.max_direction_deviation_deg

        # Verify type discriminator
        assert restored.type == params.type

        # Verify evaluator type
        assert restored.evaluator.type == params.evaluator.type

    @settings(max_examples=20)
    @given(params=valid_evolutionary_params())
    def test_dict_round_trip(self, params: EvolutionaryInfillGeneratorParameters) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 10: Serialization Round-Trip**

        *For any* valid EvolutionaryInfillGeneratorParameters, serializing to dict
        and deserializing back SHALL produce parameters equal to the original.

        **Validates: Requirements 12.1, 12.2**
        """
        # Serialize to dict
        params_dict = params.model_dump()

        # Deserialize from dict
        restored = EvolutionaryInfillGeneratorParameters.model_validate(params_dict)

        # Verify all baseline parameters match
        assert restored.num_rods == params.num_rods
        assert restored.num_layers == params.num_layers
        assert restored.main_direction_range_min_deg == params.main_direction_range_min_deg
        assert restored.main_direction_range_max_deg == params.main_direction_range_max_deg
        assert restored.min_anchor_distance_cm == params.min_anchor_distance_cm
        assert restored.infill_weight_per_meter_kg_m == params.infill_weight_per_meter_kg_m

        # Verify all evolutionary parameters match
        assert restored.max_iterations == params.max_iterations
        assert restored.max_duration_sec == params.max_duration_sec
        assert restored.improvement_threshold == params.improvement_threshold
        assert restored.stagnation_limit == params.stagnation_limit
        assert restored.max_direction_deviation_deg == params.max_direction_deviation_deg

        # Verify type discriminator
        assert restored.type == params.type

        # Verify evaluator type
        assert restored.evaluator.type == params.evaluator.type


class TestDefaultsSerializationRoundTrip:
    """Tests for EvolutionaryInfillGeneratorDefaults serialization."""

    def test_defaults_to_dict_round_trip(self) -> None:
        """
        **Feature: evolutionary-infill-generator, Property 10: Serialization Round-Trip**

        Test that EvolutionaryInfillGeneratorDefaults can be serialized to dict
        and deserialized back to an equivalent object.

        **Validates: Requirements 12.2**
        """
        from dataclasses import asdict

        original = EvolutionaryInfillGeneratorDefaults()

        # Serialize to dict
        defaults_dict = asdict(original)

        # Deserialize from dict
        restored = EvolutionaryInfillGeneratorDefaults(**defaults_dict)

        # Verify all baseline parameters match
        assert restored.num_rods == original.num_rods
        assert restored.num_layers == original.num_layers
        assert restored.main_direction_range_min_deg == original.main_direction_range_min_deg
        assert restored.main_direction_range_max_deg == original.main_direction_range_max_deg
        assert restored.min_anchor_distance_cm == original.min_anchor_distance_cm
        assert restored.infill_weight_per_meter_kg_m == original.infill_weight_per_meter_kg_m

        # Verify all evolutionary parameters match
        assert restored.max_iterations == original.max_iterations
        assert restored.max_duration_sec == original.max_duration_sec
        assert restored.improvement_threshold == original.improvement_threshold
        assert restored.stagnation_limit == original.stagnation_limit
        assert restored.max_direction_deviation_deg == original.max_direction_deviation_deg
