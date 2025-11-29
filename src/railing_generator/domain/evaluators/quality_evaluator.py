"""Quality Evaluator implementation."""

import math

import shapely
from shapely.geometry import Polygon
from shapely.ops import polygonize

from railing_generator.domain.evaluators.evaluator import Evaluator
from railing_generator.domain.evaluators.quality_evaluator_parameters import (
    QualityEvaluatorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill


class QualityEvaluator(Evaluator):
    """
    Quality Evaluator that scores arrangements using multiple weighted criteria.

    This evaluator provides detailed fitness scoring based on:
    - Hole uniformity: Prefer similar hole areas
    - Incircle uniformity: Prefer uniform incircle radii
    - Angle distribution: Penalize rods too vertical or too angled
    - Anchor spacing: Prefer evenly distributed anchor points

    The evaluator combines these criteria using configurable weights to produce
    a single fitness score. It also enforces hard constraints like maximum hole area.

    Behavior:
        - evaluate(): Returns weighted fitness score (0.0-1.0, higher is better)
        - is_acceptable(): Checks if arrangement meets minimum criteria
    """

    def __init__(self, params: QualityEvaluatorParameters) -> None:
        """
        Initialize the Quality Evaluator.

        Args:
            params: Evaluator parameters with criteria weights
        """
        self.params = params

    def evaluate(self, infill: RailingInfill, frame: RailingFrame) -> float:
        """
        Evaluate the quality of an infill arrangement.

        Calculates a weighted fitness score based on multiple quality criteria.
        Higher scores indicate better quality arrangements.

        Args:
            infill: The infill arrangement to evaluate
            frame: The railing frame containing the infill

        Returns:
            Fitness score between 0.0 and 1.0 (higher is better)

        Note:
            TODO(Task 6.9): Implement remaining quality criteria (anchor spacing)
        """
        # Identify holes in the arrangement
        holes = self._identify_holes(infill, frame)

        # Calculate hole uniformity score
        hole_uniformity_score = self._calculate_hole_uniformity(holes)

        # Calculate incircle uniformity score
        incircle_uniformity_score = self._calculate_incircle_uniformity(holes)

        # Calculate angle distribution score
        angle_distribution_score = self._calculate_angle_distribution(infill)

        # TODO(Task 6.9): Implement remaining quality criteria
        # anchor_spacing_score = self._calculate_anchor_spacing(infill, frame)

        # Combine implemented criteria with their weights
        fitness = (
            self.params.hole_uniformity_weight * hole_uniformity_score
            + self.params.incircle_uniformity_weight * incircle_uniformity_score
            + self.params.angle_distribution_weight * angle_distribution_score
        )

        # Normalize by total weight to keep score in 0-1 range
        total_weight = (
            self.params.hole_uniformity_weight
            + self.params.incircle_uniformity_weight
            + self.params.angle_distribution_weight
        )
        if total_weight > 0:
            fitness = fitness / total_weight

        return fitness

    def is_acceptable(self, infill: RailingInfill, frame: RailingFrame) -> bool:
        """
        Check if an infill arrangement meets minimum acceptance criteria.

        Verifies that the arrangement satisfies hard constraints like
        maximum hole area and completeness. This is used to reject invalid
        arrangements before detailed fitness scoring.

        Args:
            infill: The infill arrangement to check
            frame: The railing frame containing the infill

        Returns:
            True if the arrangement is acceptable, False otherwise
        """
        # Reject incomplete infills (not all requested rods were generated)
        if not infill.is_complete:
            return False

        # Identify holes in the arrangement
        holes = self._identify_holes(infill, frame)

        # Check maximum hole area constraint
        for hole in holes:
            if hole.area > self.params.max_hole_area_cm2:
                return False

        return True

    def _identify_holes(self, infill: RailingInfill, frame: RailingFrame) -> list[Polygon]:
        """
        Identify all holes in the infill arrangement.

        Uses shapely.node() to create a noded network (splits lines at
        intersection points), then polygonize() to extract enclosed polygons.

        This is necessary because rods can cross each other (different layers),
        and polygonize() requires lines to meet at endpoints. The node() function
        adds nodes at all intersection points, creating a proper network.

        Args:
            infill: The infill arrangement
            frame: The railing frame

        Returns:
            List of Polygon objects representing holes
        """
        # Combine all rod geometries (frame + infill)
        all_rods = [rod.geometry for rod in (frame.rods + infill.rods)]
        collection = shapely.GeometryCollection(all_rods)

        # Create noded network (splits lines at intersection points)
        # This is critical because rods can cross each other (different layers)
        noded = shapely.node(collection)

        # Extract enclosed polygons (holes)
        holes = list(polygonize(noded.geoms))
        return holes

    def _calculate_incircle_uniformity(self, holes: list[Polygon]) -> float:
        """
        Calculate incircle radius uniformity score (0.0-1.0).

        Measures how uniform the incircle radii are across all holes.
        The incircle (inscribed circle) is the largest circle that fits
        inside a polygon. Uniform incircle radii indicate consistent
        hole sizes and shapes.

        Uses coefficient of variation (CV = std_dev / mean) to measure uniformity.
        Lower CV means more uniform radii, which gets a higher score.

        Args:
            holes: List of Polygon objects representing holes

        Returns:
            Score between 0.0 and 1.0 (higher is better, 1.0 = perfect uniformity)
        """
        if len(holes) == 0:
            return 1.0  # No holes = perfect uniformity

        if len(holes) == 1:
            return 1.0  # Single hole = perfect uniformity

        # Calculate incircle radius for each hole
        radii = [self._calculate_incircle_radius(hole) for hole in holes]

        # Calculate mean and standard deviation
        mean_radius = sum(radii) / len(radii)

        if mean_radius == 0:
            return 0.0  # Degenerate case

        variance = sum((r - mean_radius) ** 2 for r in radii) / len(radii)
        std_dev = math.sqrt(variance)

        # Calculate coefficient of variation (CV)
        cv = std_dev / mean_radius

        # Convert CV to score (0-1 range, lower CV = higher score)
        # Use exponential decay: score = e^(-k * CV)
        # k=2 gives good sensitivity: CV=0 → score=1.0, CV=0.5 → score=0.37, CV=1.0 → score=0.14
        score = math.exp(-2.0 * cv)

        return score

    def _calculate_incircle_radius(self, polygon: Polygon) -> float:
        """
        Calculate the radius of the inscribed circle (incircle) for a polygon.

        Uses Shapely's maximum_inscribed_circle() function which finds the
        largest circle that is fully contained within the polygon. This is
        the exact maximum inscribed circle, not an approximation.

        The function returns a LineString where the first point is the center
        and the second point is on the boundary. The length of this LineString
        is the radius.

        Args:
            polygon: Shapely Polygon object

        Returns:
            Exact incircle radius in cm
        """
        # Use Shapely's built-in maximum inscribed circle function
        # Returns a LineString from center to boundary
        mic_linestring = shapely.maximum_inscribed_circle(polygon)

        # The length of the LineString is the radius
        radius = mic_linestring.length

        return radius

    def _calculate_hole_uniformity(self, holes: list[Polygon]) -> float:
        """
        Calculate hole area uniformity score (0.0-1.0).

        Measures how uniform the hole areas are across all holes.
        Uniform hole areas indicate consistent spacing and arrangement quality.

        Uses coefficient of variation (CV = std_dev / mean) to measure uniformity.
        Lower CV means more uniform areas, which gets a higher score.

        Args:
            holes: List of Polygon objects representing holes

        Returns:
            Score between 0.0 and 1.0 (higher is better, 1.0 = perfect uniformity)
        """
        if len(holes) == 0:
            return 1.0  # No holes = perfect uniformity

        if len(holes) == 1:
            return 1.0  # Single hole = perfect uniformity

        # Calculate area for each hole
        areas = [hole.area for hole in holes]

        # Calculate mean and standard deviation
        mean_area = sum(areas) / len(areas)

        if mean_area == 0:
            return 0.0  # Degenerate case

        variance = sum((a - mean_area) ** 2 for a in areas) / len(areas)
        std_dev = math.sqrt(variance)

        # Calculate coefficient of variation (CV)
        cv = std_dev / mean_area

        # Convert CV to score (0-1 range, lower CV = higher score)
        # Use exponential decay: score = e^(-k * CV)
        # k=2 gives good sensitivity: CV=0 → score=1.0, CV=0.5 → score=0.37, CV=1.0 → score=0.14
        score = math.exp(-2.0 * cv)

        return score

    def _calculate_angle_distribution(self, infill: RailingInfill) -> float:
        """
        Calculate rod angle distribution score (0.0-1.0).

        Measures the standard deviation of angles. Lower standard deviation
        means angles are clustered together (bad), higher standard deviation
        means angles are spread out (good).

        Args:
            infill: The infill arrangement to evaluate

        Returns:
            Score between 0.0 and 1.0 (higher is better)
        """
        if len(infill.rods) <= 1:
            return 1.0  # Single rod or no rods = perfect distribution

        # Calculate angle from vertical for each rod
        angles = [rod.angle_from_vertical_deg for rod in infill.rods]

        # Calculate standard deviation
        mean_angle = sum(angles) / len(angles)
        variance = sum((a - mean_angle) ** 2 for a in angles) / len(angles)
        std_dev = math.sqrt(variance)

        # Convert std_dev to score
        # Higher std_dev = better distribution (up to a point)
        # Use sigmoid-like function: score = 1 - exp(-k * std_dev)
        # k=0.05 gives good sensitivity:
        #   std_dev=0° → score=0.0 (all same angle)
        #   std_dev=10° → score=0.39
        #   std_dev=20° → score=0.63
        #   std_dev=30° → score=0.78
        score = 1.0 - math.exp(-0.05 * std_dev)

        return score

    # TODO(Task 6.9): Implement remaining quality criteria methods
    # def _calculate_anchor_spacing(
    #     self, infill: RailingInfill, frame: RailingFrame
    # ) -> tuple[float, float]:
    #     """
    #     Calculate anchor spacing scores for horizontal and vertical segments.
    #
    #     Returns:
    #         Tuple of (horizontal_score, vertical_score) each in range 0.0-1.0
    #     """
    #     pass
