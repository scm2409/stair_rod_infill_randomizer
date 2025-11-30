"""Statistics for infill generation process."""

from dataclasses import dataclass


@dataclass
class GenerationStatistics:
    """
    Statistics collected during infill generation.

    Tracks success and failure counts for various constraints to help
    diagnose why generation succeeds or fails.
    """

    # Success metrics
    rods_created: int = 0
    rods_requested: int = 0

    # Failure reasons
    too_short: int = 0
    too_long: int = 0
    outside_boundary: int = 0
    angle_too_large: int = 0
    crosses_same_layer: int = 0
    no_anchors_left: int = 0

    # Evaluator rejection tracking
    evaluator_rejections_total: int = 0
    evaluator_rejections_incomplete: int = 0
    evaluator_rejections_hole_too_large: int = 0
    evaluator_rejections_hole_too_small: int = 0

    # Generation metadata
    iterations_used: int = 0
    duration_sec: float = 0.0

    @property
    def total_failures(self) -> int:
        """Calculate total number of failures."""
        return (
            self.too_short
            + self.too_long
            + self.outside_boundary
            + self.angle_too_large
            + self.crosses_same_layer
            + self.no_anchors_left
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.rods_requested == 0:
            return 0.0
        return (self.rods_created / self.rods_requested) * 100

    def __str__(self) -> str:
        """Generate human-readable statistics summary."""
        lines = [
            "Generation Statistics:",
            f"  Rods: {self.rods_created}/{self.rods_requested} ({self.success_rate:.1f}%)",
            f"  Iterations: {self.iterations_used}",
            f"  Duration: {self.duration_sec:.2f}s",
            "",
            "Failure Reasons:",
            f"  Too short: {self.too_short}",
            f"  Too long: {self.too_long}",
            f"  Outside boundary: {self.outside_boundary}",
            f"  Angle too large: {self.angle_too_large}",
            f"  Crosses same layer: {self.crosses_same_layer}",
            f"  No anchors left: {self.no_anchors_left}",
            f"  Total failures: {self.total_failures}",
            "",
            "Evaluator Rejections:",
            f"  Total arrangements rejected: {self.evaluator_rejections_total}",
            f"  Incomplete: {self.evaluator_rejections_incomplete}",
            f"  Hole too large: {self.evaluator_rejections_hole_too_large}",
            f"  Hole too small: {self.evaluator_rejections_hole_too_small}",
        ]
        return "\n".join(lines)
