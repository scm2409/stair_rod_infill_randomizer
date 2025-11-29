"""Default configuration for Quality Evaluator."""

from dataclasses import dataclass


@dataclass
class QualityEvaluatorDefaults:
    """
    Default configuration for Quality Evaluator.

    Contains both acceptance criteria thresholds and quality criteria weights.
    All weights should sum to approximately 1.0.

    Loaded from: conf/evaluators/quality.yaml

    Attributes:
        max_hole_area_cm2: Maximum allowed hole area in square centimeters
        min_hole_area_cm2: Minimum allowed hole area in square centimeters
        hole_uniformity_weight: Weight for hole area uniformity (0.0-1.0)
        incircle_uniformity_weight: Weight for incircle radius uniformity (0.0-1.0)
        angle_distribution_weight: Weight for rod angle distribution (0.0-1.0)
        anchor_spacing_horizontal_weight: Weight for horizontal anchor spacing (0.0-1.0)
        anchor_spacing_vertical_weight: Weight for vertical anchor spacing (0.0-1.0)
    """

    # Acceptance criteria thresholds
    max_hole_area_cm2: float = 10000.0
    min_hole_area_cm2: float = 10.0

    # Quality criteria weights
    hole_uniformity_weight: float = 0.3
    incircle_uniformity_weight: float = 0.2
    angle_distribution_weight: float = 0.2
    anchor_spacing_horizontal_weight: float = 0.15
    anchor_spacing_vertical_weight: float = 0.15
