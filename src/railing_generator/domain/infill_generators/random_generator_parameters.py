"""Parameters for the random infill generator."""

from abc import ABC
from dataclasses import dataclass

from pydantic import BaseModel, Field

from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorDefaults,
    InfillGeneratorParameters,
)


@dataclass
class RandomGeneratorDefaultsBase(ABC):
    """
    Base class for random generator default values.

    This serves as the base for all random generator variants (v1, v2, etc.).
    """

    num_rods: int
    min_rod_length_cm: float
    max_rod_length_cm: float
    max_angle_deviation_deg: float
    num_layers: int
    max_iterations: int
    max_duration_sec: float
    infill_weight_per_meter_kg_m: float


class RandomGeneratorParametersBase(BaseModel, ABC):
    """
    Base class for random generator runtime parameters.

    This serves as the base for all random generator variants (v1, v2, etc.).
    """

    num_rods: int
    min_rod_length_cm: float
    max_rod_length_cm: float
    max_angle_deviation_deg: float
    num_layers: int
    max_iterations: int
    max_duration_sec: float
    infill_weight_per_meter_kg_m: float


@dataclass
class RandomGeneratorDefaults(InfillGeneratorDefaults, RandomGeneratorDefaultsBase):
    """
    Default values for random generator loaded from Hydra configuration.

    These defaults are loaded from conf/generators/random.yaml.
    """

    num_rods: int = 30
    min_rod_length_cm: float = 50.0
    max_rod_length_cm: float = 200.0
    max_angle_deviation_deg: float = 30.0
    num_layers: int = 2
    min_anchor_distance_cm: float = 10.0
    max_iterations: int = 1000
    max_duration_sec: float = 60.0
    infill_weight_per_meter_kg_m: float = 0.3


class RandomGeneratorParameters(InfillGeneratorParameters, RandomGeneratorParametersBase):
    """
    Runtime parameters for random generator with Pydantic validation.

    These parameters control the behavior of the random infill generator.
    """

    num_rods: int = Field(ge=1, le=200, description="Number of infill rods")
    min_rod_length_cm: float = Field(gt=0, description="Minimum rod length in cm")
    max_rod_length_cm: float = Field(gt=0, description="Maximum rod length in cm")
    max_angle_deviation_deg: float = Field(
        ge=0, le=45, description="Max angle deviation from vertical in degrees"
    )
    num_layers: int = Field(ge=1, le=5, description="Number of layers")
    min_anchor_distance_cm: float = Field(
        gt=0, description="Minimum distance between anchor points in cm"
    )
    max_iterations: int = Field(ge=1, description="Maximum iterations")
    max_duration_sec: float = Field(gt=0, description="Maximum duration in seconds")
    infill_weight_per_meter_kg_m: float = Field(
        gt=0, description="Infill rod weight per meter in kg/m"
    )

    @classmethod
    def from_defaults(cls, defaults: RandomGeneratorDefaults) -> "RandomGeneratorParameters":
        """
        Create parameters from config defaults.

        Args:
            defaults: Default values from Hydra configuration

        Returns:
            RandomGeneratorParameters instance with default values
        """
        return cls(
            num_rods=defaults.num_rods,
            min_rod_length_cm=defaults.min_rod_length_cm,
            max_rod_length_cm=defaults.max_rod_length_cm,
            max_angle_deviation_deg=defaults.max_angle_deviation_deg,
            num_layers=defaults.num_layers,
            min_anchor_distance_cm=defaults.min_anchor_distance_cm,
            max_iterations=defaults.max_iterations,
            max_duration_sec=defaults.max_duration_sec,
            infill_weight_per_meter_kg_m=defaults.infill_weight_per_meter_kg_m,
        )
