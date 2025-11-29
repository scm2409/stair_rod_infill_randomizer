"""Parameters for Quality Evaluator."""

from typing import Literal

from pydantic import BaseModel, Field

from railing_generator.domain.evaluators.evaluator_parameters import EvaluatorParameters
from railing_generator.domain.evaluators.quality_evaluator_defaults import (
    QualityEvaluatorDefaults,
)


class QualityEvaluatorParameters(EvaluatorParameters):
    """
    Parameters for Quality Evaluator.

    The Quality Evaluator uses multiple weighted criteria to assess
    infill arrangement quality. It provides detailed fitness scoring
    for optimization and rejects arrangements that exceed maximum hole area
    or fall below minimum hole area.

    Attributes:
        type: Evaluator type discriminator (always "quality")
        max_hole_area_cm2: Maximum allowed hole area in square centimeters
        min_hole_area_cm2: Minimum allowed hole area in square centimeters
        hole_uniformity_weight: Weight for hole area uniformity criterion
        incircle_uniformity_weight: Weight for incircle radius uniformity criterion
        angle_distribution_weight: Weight for rod angle distribution criterion
        anchor_spacing_horizontal_weight: Weight for horizontal anchor spacing criterion
        anchor_spacing_vertical_weight: Weight for vertical anchor spacing criterion
    """

    type: Literal["quality"] = Field(default="quality", description="Evaluator type discriminator")

    # Acceptance criteria thresholds
    max_hole_area_cm2: float = Field(
        gt=0, description="Maximum allowed hole area in square centimeters"
    )
    min_hole_area_cm2: float = Field(
        gt=0, description="Minimum allowed hole area in square centimeters"
    )

    # Quality criteria weights (should sum to ~1.0)
    hole_uniformity_weight: float = Field(ge=0, le=1, description="Weight for hole area uniformity")
    incircle_uniformity_weight: float = Field(
        ge=0, le=1, description="Weight for incircle radius uniformity"
    )
    angle_distribution_weight: float = Field(
        ge=0, le=1, description="Weight for rod angle distribution"
    )
    anchor_spacing_horizontal_weight: float = Field(
        ge=0, le=1, description="Weight for horizontal anchor spacing"
    )
    anchor_spacing_vertical_weight: float = Field(
        ge=0, le=1, description="Weight for vertical anchor spacing"
    )

    @classmethod
    def from_defaults(cls, defaults: QualityEvaluatorDefaults) -> "QualityEvaluatorParameters":
        """
        Create parameters from default configuration.

        Args:
            defaults: Default configuration from Hydra config

        Returns:
            QualityEvaluatorParameters instance with default values
        """
        return cls(
            max_hole_area_cm2=defaults.max_hole_area_cm2,
            min_hole_area_cm2=defaults.min_hole_area_cm2,
            hole_uniformity_weight=defaults.hole_uniformity_weight,
            incircle_uniformity_weight=defaults.incircle_uniformity_weight,
            angle_distribution_weight=defaults.angle_distribution_weight,
            anchor_spacing_horizontal_weight=defaults.anchor_spacing_horizontal_weight,
            anchor_spacing_vertical_weight=defaults.anchor_spacing_vertical_weight,
        )
