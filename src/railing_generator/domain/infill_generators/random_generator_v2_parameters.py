"""Parameters for the random infill generator v2."""

from dataclasses import dataclass
from typing import Literal, Union

from pydantic import Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from railing_generator.domain.evaluators.evaluator_parameters import EvaluatorParameters
from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
    PassThroughEvaluatorParameters,
)
from railing_generator.domain.evaluators.quality_evaluator_parameters import (
    QualityEvaluatorParameters,
)
from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorDefaults,
    InfillGeneratorParameters,
)
from railing_generator.domain.infill_generators.random_generator_parameters import (
    RandomGeneratorDefaultsBase,
    RandomGeneratorParametersBase,
)

# Discriminated union for evaluator parameters
# Pydantic will automatically select the correct type based on the 'type' field
EvaluatorParametersUnion = Union[
    PassThroughEvaluatorParameters,
    QualityEvaluatorParameters,
]


@dataclass
class RandomGeneratorDefaultsV2(InfillGeneratorDefaults, RandomGeneratorDefaultsBase):
    """
    Default values for random generator v2 loaded from Hydra configuration.

    These defaults are loaded from conf/generators/random_v2.yaml.
    """

    # Base parameters
    num_rods: int = 30
    min_rod_length_cm: float = 50.0
    max_rod_length_cm: float = 200.0
    max_angle_deviation_deg: float = 40.0
    num_layers: int = 3
    max_iterations: int = 1000
    max_duration_sec: float = 60.0
    infill_weight_per_meter_kg_m: float = 0.3

    # Evaluation loop parameters
    max_evaluation_attempts: int = 10
    max_evaluation_duration_sec: float = 60.0
    min_acceptable_fitness: float = 0.7

    # V2-specific parameters
    min_anchor_distance_vertical_cm: float = 15.0
    min_anchor_distance_other_cm: float = 5.0
    main_direction_range_min_deg: float = -30.0
    main_direction_range_max_deg: float = 10.0
    random_angle_deviation_deg: float = 20.0
    # Note: evaluator parameters stored separately, not in defaults


class RandomGeneratorParametersV2(InfillGeneratorParameters, RandomGeneratorParametersBase):
    """
    Runtime parameters for random generator v2 with Pydantic validation.

    These parameters control the behavior of the random infill generator v2.
    """

    type: Literal["random_v2"] = "random_v2"

    # Base parameters
    num_rods: int = Field(ge=1, le=200, description="Number of infill rods")
    min_rod_length_cm: float = Field(gt=0, description="Minimum rod length in cm")
    max_rod_length_cm: float = Field(gt=0, description="Maximum rod length in cm")
    max_angle_deviation_deg: float = Field(
        ge=0, le=75, description="Max angle deviation from vertical in degrees"
    )
    num_layers: int = Field(ge=1, le=5, description="Number of layers")
    max_iterations: int = Field(ge=1, description="Maximum iterations per arrangement (inner loop)")
    max_duration_sec: float = Field(
        gt=0, description="Maximum duration per arrangement in seconds (inner loop)"
    )
    infill_weight_per_meter_kg_m: float = Field(
        gt=0, description="Infill rod weight per meter in kg/m"
    )

    # Evaluation loop parameters (outer loop)
    max_evaluation_attempts: int = Field(
        ge=1, description="Maximum number of arrangements to generate and evaluate (outer loop)"
    )
    max_evaluation_duration_sec: float = Field(
        gt=0, description="Maximum total evaluation duration in seconds (outer loop)"
    )
    min_acceptable_fitness: float = Field(
        ge=0,
        le=1,
        description="Minimum fitness score to accept early and stop evaluation loop",
    )

    # V2-specific parameters
    min_anchor_distance_vertical_cm: float = Field(
        gt=0, description="Minimum distance between anchor points on vertical frame rods in cm"
    )
    min_anchor_distance_other_cm: float = Field(
        gt=0,
        description="Minimum distance between anchor points on horizontal/sloped frame rods in cm",
    )
    main_direction_range_min_deg: float = Field(
        ge=-90, le=90, description="Minimum angle for layer main directions (degrees from vertical)"
    )
    main_direction_range_max_deg: float = Field(
        ge=-90, le=90, description="Maximum angle for layer main directions (degrees from vertical)"
    )
    random_angle_deviation_deg: float = Field(
        ge=0, description="Random angle deviation from layer main direction (±degrees)"
    )

    # Nested evaluator parameters (discriminated union)
    evaluator: EvaluatorParametersUnion = Field(
        default_factory=PassThroughEvaluatorParameters,
        discriminator="type",
        description="Evaluator configuration (passthrough, quality, etc.)",
    )

    @field_validator("main_direction_range_max_deg")
    @classmethod
    def validate_direction_range(cls, v: float, info: ValidationInfo) -> float:
        """Ensure max > min for direction range."""
        if "main_direction_range_min_deg" in info.data:
            if v <= info.data["main_direction_range_min_deg"]:
                raise ValueError(
                    "main_direction_range_max_deg must be greater than main_direction_range_min_deg"
                )
        return v

    @classmethod
    def from_defaults(cls, defaults: RandomGeneratorDefaultsV2) -> "RandomGeneratorParametersV2":
        """
        Create parameters from config defaults.

        Args:
            defaults: Default values from Hydra configuration

        Returns:
            RandomGeneratorParametersV2 instance with default values
        """
        return cls(
            num_rods=defaults.num_rods,
            min_rod_length_cm=defaults.min_rod_length_cm,
            max_rod_length_cm=defaults.max_rod_length_cm,
            max_angle_deviation_deg=defaults.max_angle_deviation_deg,
            num_layers=defaults.num_layers,
            max_iterations=defaults.max_iterations,
            max_duration_sec=defaults.max_duration_sec,
            infill_weight_per_meter_kg_m=defaults.infill_weight_per_meter_kg_m,
            max_evaluation_attempts=defaults.max_evaluation_attempts,
            max_evaluation_duration_sec=defaults.max_evaluation_duration_sec,
            min_acceptable_fitness=defaults.min_acceptable_fitness,
            min_anchor_distance_vertical_cm=defaults.min_anchor_distance_vertical_cm,
            min_anchor_distance_other_cm=defaults.min_anchor_distance_other_cm,
            main_direction_range_min_deg=defaults.main_direction_range_min_deg,
            main_direction_range_max_deg=defaults.main_direction_range_max_deg,
            random_angle_deviation_deg=defaults.random_angle_deviation_deg,
            evaluator=PassThroughEvaluatorParameters(),  # Default evaluator
        )
