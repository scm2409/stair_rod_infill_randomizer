"""Default configuration for Quality Evaluator criteria."""

from dataclasses import dataclass


@dataclass
class QualityEvaluatorCriteriaDefaults:
    """
    Default configuration for Quality Evaluator criteria weights.

    These weights determine the relative importance of each quality criterion
    in the overall fitness score. All weights should sum to approximately 1.0.

    Loaded from: conf/evaluators/criteria.yaml

    Attributes:
        hole_uniformity_weight: Weight for hole area uniformity (0.0-1.0)
        incircle_uniformity_weight: Weight for incircle radius uniformity (0.0-1.0)
        angle_distribution_weight: Weight for rod angle distribution (0.0-1.0)
        anchor_spacing_horizontal_weight: Weight for horizontal anchor spacing (0.0-1.0)
        anchor_spacing_vertical_weight: Weight for vertical anchor spacing (0.0-1.0)
    """

    hole_uniformity_weight: float = 0.3
    incircle_uniformity_weight: float = 0.2
    angle_distribution_weight: float = 0.2
    anchor_spacing_horizontal_weight: float = 0.15
    anchor_spacing_vertical_weight: float = 0.15
