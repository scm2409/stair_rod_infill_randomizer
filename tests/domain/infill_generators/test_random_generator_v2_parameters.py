"""Tests for RandomGeneratorV2 parameters."""

import pytest
from pydantic import ValidationError

from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
    RandomGeneratorDefaultsV2,
    RandomGeneratorParametersV2,
)


def test_random_generator_v2_defaults_creation() -> None:
    """Test creating RandomGeneratorDefaultsV2."""
    defaults = RandomGeneratorDefaultsV2()

    assert defaults.num_rods == 45
    assert defaults.min_rod_length_cm == 50.0
    assert defaults.max_rod_length_cm == 200.0
    assert defaults.max_angle_deviation_deg == 30.0
    assert defaults.num_layers == 3
    assert defaults.max_iterations == 1000
    assert defaults.max_duration_sec == 60.0
    assert defaults.infill_weight_per_meter_kg_m == 0.3
    assert defaults.max_evaluation_attempts == 10
    assert defaults.max_evaluation_duration_sec == 60.0
    assert defaults.min_acceptable_fitness == 0.7
    assert defaults.min_anchor_distance_vertical_cm == 15.0
    assert defaults.min_anchor_distance_other_cm == 5.0
    assert defaults.main_direction_range_min_deg == -50.0
    assert defaults.main_direction_range_max_deg == 20.0
    assert defaults.random_angle_deviation_deg == 30.0


def test_random_generator_v2_parameters_creation() -> None:
    """Test creating RandomGeneratorParametersV2."""
    params = RandomGeneratorParametersV2(
        num_rods=50,
        min_rod_length_cm=50.0,
        max_rod_length_cm=200.0,
        max_angle_deviation_deg=30.0,
        num_layers=2,
        max_iterations=1000,
        max_duration_sec=60.0,
        infill_weight_per_meter_kg_m=0.3,
        max_evaluation_attempts=10,
        max_evaluation_duration_sec=60.0,
        min_acceptable_fitness=0.7,
        min_anchor_distance_vertical_cm=5.0,
        min_anchor_distance_other_cm=10.0,
        main_direction_range_min_deg=-30.0,
        main_direction_range_max_deg=30.0,
        random_angle_deviation_deg=30.0,
    )

    assert params.num_rods == 50
    assert params.min_rod_length_cm == 50.0
    assert params.max_rod_length_cm == 200.0
    assert params.max_angle_deviation_deg == 30.0
    assert params.num_layers == 2
    assert params.max_iterations == 1000
    assert params.max_duration_sec == 60.0
    assert params.infill_weight_per_meter_kg_m == 0.3
    assert params.max_evaluation_attempts == 10
    assert params.max_evaluation_duration_sec == 60.0
    assert params.min_acceptable_fitness == 0.7
    assert params.min_anchor_distance_vertical_cm == 5.0
    assert params.min_anchor_distance_other_cm == 10.0
    assert params.main_direction_range_min_deg == -30.0
    assert params.main_direction_range_max_deg == 30.0
    assert params.random_angle_deviation_deg == 30.0


def test_random_generator_v2_parameters_from_defaults() -> None:
    """Test creating parameters from defaults."""
    defaults = RandomGeneratorDefaultsV2(
        num_rods=75, min_rod_length_cm=40.0, min_anchor_distance_vertical_cm=3.0
    )
    params = RandomGeneratorParametersV2.from_defaults(defaults)

    assert params.num_rods == 75
    assert params.min_rod_length_cm == 40.0
    assert params.min_anchor_distance_vertical_cm == 3.0


def test_random_generator_v2_parameters_validation_min_anchor_distance_vertical() -> None:
    """Test validation rejects non-positive min_anchor_distance_vertical_cm."""
    with pytest.raises(ValidationError):
        RandomGeneratorParametersV2(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=2,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
            max_evaluation_attempts=10,
            max_evaluation_duration_sec=60.0,
            min_acceptable_fitness=0.7,
            min_anchor_distance_vertical_cm=0.0,  # Must be positive
            min_anchor_distance_other_cm=10.0,
            main_direction_range_min_deg=-30.0,
            main_direction_range_max_deg=30.0,
            random_angle_deviation_deg=30.0,
        )


def test_random_generator_v2_parameters_validation_min_anchor_distance_other() -> None:
    """Test validation rejects non-positive min_anchor_distance_other_cm."""
    with pytest.raises(ValidationError):
        RandomGeneratorParametersV2(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=2,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
            max_evaluation_attempts=10,
            max_evaluation_duration_sec=60.0,
            min_acceptable_fitness=0.7,
            min_anchor_distance_vertical_cm=5.0,
            min_anchor_distance_other_cm=0.0,  # Must be positive
            main_direction_range_min_deg=-30.0,
            main_direction_range_max_deg=30.0,
            random_angle_deviation_deg=30.0,
        )


def test_random_generator_v2_parameters_validation_direction_range() -> None:
    """Test validation rejects invalid direction range (max <= min)."""
    with pytest.raises(ValidationError):
        RandomGeneratorParametersV2(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=2,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
            max_evaluation_attempts=10,
            max_evaluation_duration_sec=60.0,
            min_acceptable_fitness=0.7,
            min_anchor_distance_vertical_cm=5.0,
            min_anchor_distance_other_cm=10.0,
            main_direction_range_min_deg=30.0,
            main_direction_range_max_deg=30.0,  # Must be > min
            random_angle_deviation_deg=30.0,
        )


def test_random_generator_v2_parameters_validation_random_angle_deviation() -> None:
    """Test validation rejects negative random_angle_deviation_deg."""
    with pytest.raises(ValidationError):
        RandomGeneratorParametersV2(
            num_rods=50,
            min_rod_length_cm=50.0,
            max_rod_length_cm=200.0,
            max_angle_deviation_deg=30.0,
            num_layers=2,
            max_iterations=1000,
            max_duration_sec=60.0,
            infill_weight_per_meter_kg_m=0.3,
            max_evaluation_attempts=10,
            max_evaluation_duration_sec=60.0,
            min_acceptable_fitness=0.7,
            min_anchor_distance_vertical_cm=5.0,
            min_anchor_distance_other_cm=10.0,
            main_direction_range_min_deg=-30.0,
            main_direction_range_max_deg=30.0,
            random_angle_deviation_deg=-1.0,  # Must be non-negative
        )
