"""Parameters for Quality Evaluator."""

from typing import Literal

from pydantic import BaseModel, Field

from railing_generator.domain.evaluators.evaluator_parameters import EvaluatorParameters
from railing_generator.domain.evaluators.quality_evaluator_criteria_defaults import (
    QualityEvaluatorCriteriaDefaults,
)


class QualityEvaluatorParameters(EvaluatorParameters):
    """
    Parameters for Quality Evaluator.

    The Quality Evaluator uses multiple weighted criteria to assess
    infill arrangement quality. It provides detailed fitness scoring
    for optimization and rejects arrangements that exceed maximum hole area.

    Attributes:
        type: Evaluator type discriminator (always "quality")
        max_hole_area_cm2: Maximum allowed hole area in square centimeters
        hole_uniformity_weight: Weight for hole area uniformity criterion
        incircle_uniformity_weight: Weight for incircle radius uniformity criterion
        angle_distribution_weight: Weight for rod angle distribution criterion
        anchor_spacing_horizontal_weight: Weight for horizontal anchor spacing criterion
        anchor_spacing_vertical_weight: Weight for vertical anchor spacing criterion
    """

    type: Literal["quality"] = Field(default="quality", description="Evaluator type discriminator")

    # Acceptance criteria
    max_hole_area_cm2: float = Field(
        gt=0, description="Maximum allowed hole area in square centimeters"
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
    def from_defaults(
        cls, max_hole_area_cm2: float, criteria: QualityEvaluatorCriteriaDefaults
    ) -> "QualityEvaluatorParameters":
        """
        Create parameters from default configuration.

        Args:
            max_hole_area_cm2: Maximum allowed hole area
            criteria: Default criteria weights from Hydra config

        Returns:
            QualityEvaluatorParameters instance with default values
        """
        return cls(
            max_hole_area_cm2=max_hole_area_cm2,
            hole_uniformity_weight=criteria.hole_uniformity_weight,
            incircle_uniformity_weight=criteria.incircle_uniformity_weight,
            angle_distribution_weight=criteria.angle_distribution_weight,
            anchor_spacing_horizontal_weight=criteria.anchor_spacing_horizontal_weight,
            anchor_spacing_vertical_weight=criteria.anchor_spacing_vertical_weight,
        )
