"""Tests for RandomGenerator parameters."""

import pytest
from pydantic import ValidationError

from railing_generator.domain.infill_generators.random_generator_parameters import (
    RandomGeneratorDefaults,
    RandomGeneratorParameters,
)


def test_random_generator_defaults_creation() -> None:
    """Test creating RandomGeneratorDefaults."""
    defaults = RandomGeneratorDefaults()

    assert defaults.num_rods == 50
    assert defaults.min_rod_length_cm == 50.0
    assert defaults.max_rod_length_cm == 200.0
    assert defaults.max_angle_deviation_deg == 30.0
    assert defaults.num_layers == 2
    assert defaults.min_anchor_distance_cm == 10.0
    assert defaults.max_iterations == 1000
    assert defaults.max_duration_sec == 60.0
    assert defaults.infill_weight_per_meter_kg_m == 0.3


def test_random_generator_defaults_custom_values() -> None:
    """Test creating RandomGeneratorDefaults with custom values."""
    defaults = RandomGeneratorDefaults(
        num_rods=100,
        min_rod_length_cm=40.0,
        max_rod_length_cm=300.0,
        max_angle_deviation_deg=45.0,
        num_layers=3,
        min_anchor_distance_cm=15.0,
        max_iterations=2000,
        max_duration_sec=120.0,
        infill_weight_per_meter_kg_m=0.5,
    )

    assert defaults.num_rods == 100
    assert defaults.min_rod_length_cm == 40.0
    assert defaults.max_rod_length_cm == 300.0
    assert defaults.max_angle_deviation_deg == 45.0
    assert defaults.num_layers == 3
    assert defaults.min_anchor_distance_cm == 15.0
    assert defaults.max_iterations == 2000
    assert defaults.max_duration_sec == 120.0
    assert defaults.infill_weight_per_meter_kg_m == 0.5


def test_random_generator_parameters_creation() -> None:
    """Test creating RandomGeneratorParameters."""
    params = RandomGeneratorParameters(
        num_rods=50,
        min_rod_length_cm=50.0,
        max_rod_length_cm=200.0,
        max_angle_deviation_deg=30.0,
        num_layers=2,
        min_anchor_distance_cm=10.0,
        max_iterations=1000,
        max_duration_sec=60.0,
        infill_weight_per_meter_kg_m=0.3,
    )

    assert params.num_rods == 50
    assert params.min_rod_length_cm == 50.0
    assert params.max_rod_length_cm == 200.0
    assert params.max_angle_deviation_deg == 30.0
    assert params.num_layers == 2
    assert params.min_anchor_distance_cm == 10.0
    assert params.max_iterations == 1000
    assert params.max_duration_sec == 60.0
    assert params.infill_weight_per_meter_kg_m == 0.3


def test_random_generator_parameters_from_defaults() -> None:
    """Test creating parameters from defaults."""
    defaults = RandomGeneratorDefaults(num_rods=75, min_rod_length_cm=40.0, max_rod_length_cm=250.0)
    params = RandomGeneratorParameters.from_defaults(defaults)

    assert params.num_rods == 75
    assert params.min_rod_length_cm == 40.0
    assert params.max_rod_length_cm == 250.0
    assert params.max_angle_deviation_deg == 30.0  # Default value


def test_random_generator_parameters_validation_num_rods_min() -> None:
    """Test validation rejects num_rods below minimum."""
    with pytest.raises(ValidationError):
        RandomGeneratorParameters(
            num_rods=0,  # Below minimum
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=2,
            min_anchor_distance_cm=10.0,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
        )


def test_random_generator_parameters_validation_num_rods_max() -> None:
    """Test validation rejects num_rods above maximum."""
    with pytest.raises(ValidationError):
        RandomGeneratorParameters(
            num_rods=201,  # Above maximum
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=2,
            min_anchor_distance_cm=10.0,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
        )


def test_random_generator_parameters_validation_min_rod_length() -> None:
    """Test validation rejects non-positive min_rod_length_cm."""
    with pytest.raises(ValidationError):
        RandomGeneratorParameters(
            num_rods=50,
            min_rod_length_cm=0.0,  # Must be positive
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=2,
            min_anchor_distance_cm=10.0,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
        )


def test_random_generator_parameters_validation_max_rod_length() -> None:
    """Test validation rejects non-positive max_rod_length_cm."""
    with pytest.raises(ValidationError):
        RandomGeneratorParameters(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=0.0,  # Must be positive
            max_angle_deviation_deg=30.0,
            num_layers=2,
            min_anchor_distance_cm=10.0,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
        )


def test_random_generator_parameters_validation_max_angle_deviation_min() -> None:
    """Test validation rejects negative max_angle_deviation_deg."""
    with pytest.raises(ValidationError):
        RandomGeneratorParameters(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=-1.0,  # Below minimum
            num_layers=2,
            min_anchor_distance_cm=10.0,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
        )


def test_random_generator_parameters_validation_max_angle_deviation_max() -> None:
    """Test validation rejects max_angle_deviation_deg above maximum."""
    with pytest.raises(ValidationError):
        RandomGeneratorParameters(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=46.0,  # Above maximum
            num_layers=2,
            min_anchor_distance_cm=10.0,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
        )


def test_random_generator_parameters_validation_num_layers_min() -> None:
    """Test validation rejects num_layers below minimum."""
    with pytest.raises(ValidationError):
        RandomGeneratorParameters(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=0,  # Below minimum
            min_anchor_distance_cm=10.0,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
        )


def test_random_generator_parameters_validation_num_layers_max() -> None:
    """Test validation rejects num_layers above maximum."""
    with pytest.raises(ValidationError):
        RandomGeneratorParameters(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=6,  # Above maximum
            min_anchor_distance_cm=10.0,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
        )


def test_random_generator_parameters_validation_min_anchor_distance() -> None:
    """Test validation rejects non-positive min_anchor_distance_cm."""
    with pytest.raises(ValidationError):
        RandomGeneratorParameters(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=2,
            min_anchor_distance_cm=0.0,  # Must be positive
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
        )


def test_random_generator_parameters_validation_max_iterations() -> None:
    """Test validation rejects non-positive max_iterations."""
    with pytest.raises(ValidationError):
        RandomGeneratorParameters(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=2,
            min_anchor_distance_cm=10.0,
            max_iterations=0,  # Must be positive
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
        )


def test_random_generator_parameters_validation_max_duration() -> None:
    """Test validation rejects non-positive max_duration_sec."""
    with pytest.raises(ValidationError):
        RandomGeneratorParameters(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=2,
            min_anchor_distance_cm=10.0,
            max_iterations=1000,
            max_duration_sec=0.0,  # Must be positive
            infill_weight_per_meter_kg_m=0.3,
        )


def test_random_generator_parameters_validation_infill_weight() -> None:
    """Test validation rejects non-positive infill_weight_per_meter_kg_m."""
    with pytest.raises(ValidationError):
        RandomGeneratorParameters(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=2,
            min_anchor_distance_cm=10.0,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.0,  # Must be positive
        )
