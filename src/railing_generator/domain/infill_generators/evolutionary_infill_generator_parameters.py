"""Parameters for the Evolutionary Infill Generator.

The Evolutionary Infill Generator combines uniform directional baseline generation
with iterative mutation and fitness-based selection for optimization.
"""

from dataclasses import dataclass
from typing import Literal, Self, Union

from hydra.core.config_store import ConfigStore
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
class EvolutionaryInfillGeneratorDefaults(InfillGeneratorDefaults):
    """
    Default values for Evolutionary Infill Generator loaded from Hydra configuration.

    These defaults are loaded from conf/generators/evolutionary.yaml.

    Baseline parameters (same as UniformDirectionalGenerator):
        num_rods: Total number of rods to generate
        num_layers: Number of rod layers
        main_direction_range_min_deg: Minimum angle from vertical (degrees)
        main_direction_range_max_deg: Maximum angle from vertical (degrees)
        min_anchor_distance_cm: Minimum distance between anchor points (cm)
        infill_weight_per_meter_kg_m: Infill rod weight per meter (kg/m)

    Evolutionary parameters:
        max_iterations: Maximum number of mutation iterations
        max_duration_sec: Maximum generation duration in seconds
        improvement_threshold: Minimum fitness improvement to accept a mutation
        stagnation_limit: Iterations without improvement before early termination
    """

    # Baseline parameters (same as UniformDirectionalGenerator)
    num_rods: int = 30
    num_layers: int = 3
    main_direction_range_min_deg: float = -45.0
    main_direction_range_max_deg: float = 25.0
    min_anchor_distance_cm: float = 5.0
    infill_weight_per_meter_kg_m: float = 0.59

    # Evolutionary parameters
    max_iterations: int = 1000
    max_duration_sec: float = 60.0
    improvement_threshold: float = 0.001
    stagnation_limit: int = 100


class EvolutionaryInfillGeneratorParameters(InfillGeneratorParameters):
    """
    Runtime parameters for Evolutionary Infill Generator with Pydantic validation.

    These parameters control the behavior of the evolutionary optimization generator
    that combines uniform directional baseline generation with iterative mutation
    and fitness-based selection.
    """

    type: Literal["evolutionary"] = "evolutionary"

    # Baseline parameters (same as UniformDirectionalGenerator)
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

    # Evolutionary parameters
    max_iterations: int = Field(
        ge=1, le=100000, description="Maximum number of mutation iterations"
    )
    max_duration_sec: float = Field(gt=0, description="Maximum generation duration in seconds")
    improvement_threshold: float = Field(
        ge=0, le=1, description="Minimum fitness improvement to accept a mutation"
    )
    stagnation_limit: int = Field(
        ge=1, description="Iterations without improvement before early termination"
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
        cls, defaults: "EvolutionaryInfillGeneratorDefaults"
    ) -> "EvolutionaryInfillGeneratorParameters":
        """
        Create parameters from config defaults.

        Args:
            defaults: Default values from Hydra configuration

        Returns:
            EvolutionaryInfillGeneratorParameters instance with default values
        """
        return cls(
            num_rods=defaults.num_rods,
            num_layers=defaults.num_layers,
            main_direction_range_min_deg=defaults.main_direction_range_min_deg,
            main_direction_range_max_deg=defaults.main_direction_range_max_deg,
            min_anchor_distance_cm=defaults.min_anchor_distance_cm,
            infill_weight_per_meter_kg_m=defaults.infill_weight_per_meter_kg_m,
            max_iterations=defaults.max_iterations,
            max_duration_sec=defaults.max_duration_sec,
            improvement_threshold=defaults.improvement_threshold,
            stagnation_limit=defaults.stagnation_limit,
            evaluator=PassThroughEvaluatorParameters(),  # Default evaluator
        )


# Register with Hydra ConfigStore
cs = ConfigStore.instance()
cs.store(group="generators", name="evolutionary", node=EvolutionaryInfillGeneratorDefaults)
