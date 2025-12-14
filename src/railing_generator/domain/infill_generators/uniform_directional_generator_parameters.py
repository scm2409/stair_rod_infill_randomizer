"""Parameters for the Uniform Directional Generator."""

from dataclasses import dataclass
from typing import Literal, Self, Union

from pydantic import Field, model_validator

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

# Discriminated union for evaluator parameters
# Pydantic will automatically select the correct type based on the 'type' field
EvaluatorParametersUnion = Union[
    PassThroughEvaluatorParameters,
    QualityEvaluatorParameters,
]


@dataclass
class UniformDirectionalGeneratorDefaults(InfillGeneratorDefaults):
    """
    Default values for Uniform Directional Generator loaded from Hydra configuration.

    These defaults are loaded from conf/generators/uniform_directional.yaml.
    """

    num_rods: int = 30
    num_layers: int = 3
    main_direction_range_min_deg: float = -45.0
    main_direction_range_max_deg: float = 25.0
    min_anchor_distance_cm: float = 5.0
    infill_weight_per_meter_kg_m: float = 0.59


class UniformDirectionalGeneratorParameters(InfillGeneratorParameters):
    """
    Runtime parameters for Uniform Directional Generator with Pydantic validation.

    These parameters control the behavior of the deterministic uniform infill generator.
    """

    type: Literal["uniform_directional"] = "uniform_directional"

    num_rods: int = Field(ge=1, le=200, description="Total number of rods to generate")
    num_layers: int = Field(ge=1, le=10, description="Number of rod layers")
    main_direction_range_min_deg: float = Field(
        ge=-90, le=90, description="Minimum angle from vertical (degrees)"
    )
    main_direction_range_max_deg: float = Field(
        ge=-90, le=90, description="Maximum angle from vertical (degrees)"
    )
    min_anchor_distance_cm: float = Field(
        gt=0, description="Minimum distance between anchor points (cm)"
    )
    infill_weight_per_meter_kg_m: float = Field(
        gt=0, description="Infill rod weight per meter (kg/m)"
    )

    # Nested evaluator parameters (discriminated union)
    evaluator: EvaluatorParametersUnion = Field(
        default_factory=PassThroughEvaluatorParameters,
        discriminator="type",
        description="Evaluator configuration (passthrough, quality, etc.)",
    )

    @model_validator(mode="after")
    def validate_direction_range(self) -> Self:
        """Ensure main_direction_range_min_deg < main_direction_range_max_deg."""
        if self.main_direction_range_min_deg >= self.main_direction_range_max_deg:
            raise ValueError(
                "main_direction_range_min_deg must be less than main_direction_range_max_deg"
            )
        return self

    @classmethod
    def from_defaults(
        cls, defaults: "UniformDirectionalGeneratorDefaults"
    ) -> "UniformDirectionalGeneratorParameters":
        """
        Create parameters from config defaults.

        Args:
            defaults: Default values from Hydra configuration

        Returns:
            UniformDirectionalGeneratorParameters instance with default values
        """
        return cls(
            num_rods=defaults.num_rods,
            num_layers=defaults.num_layers,
            main_direction_range_min_deg=defaults.main_direction_range_min_deg,
            main_direction_range_max_deg=defaults.main_direction_range_max_deg,
            min_anchor_distance_cm=defaults.min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=defaults.infill_weight_per_meter_kg_m,
            evaluator=PassThroughEvaluatorParameters(),  # Default evaluator
        )
