"""Evaluation result with acceptance status and detailed rejection reasons."""

from dataclasses import dataclass, field


@dataclass
class RejectionReasons:
    """
    Detailed breakdown of why an arrangement was rejected.

    Tracks counts for each specific rejection criterion to enable
    detailed statistics about what constraints are failing.
    """

    incomplete: int = 0
    hole_too_large: int = 0
    hole_too_small: int = 0

    @property
    def total(self) -> int:
        """Total number of rejection reasons."""
        return self.incomplete + self.hole_too_large + self.hole_too_small

    @property
    def has_rejections(self) -> bool:
        """Check if there are any rejections."""
        return self.total > 0

    def __str__(self) -> str:
        """Generate human-readable summary."""
        parts = []
        if self.incomplete > 0:
            parts.append(f"incomplete({self.incomplete})")
        if self.hole_too_large > 0:
            parts.append(f"hole_too_large({self.hole_too_large})")
        if self.hole_too_small > 0:
            parts.append(f"hole_too_small({self.hole_too_small})")
        return ", ".join(parts) if parts else "none"


@dataclass
class EvaluationResult:
    """
    Result of evaluator acceptance check.

    Contains both the acceptance status and detailed breakdown of
    rejection reasons with counts for each criterion.
    """

    is_acceptable: bool
    rejection_reasons: RejectionReasons = field(default_factory=RejectionReasons)

    @staticmethod
    def accepted() -> "EvaluationResult":
        """Create an accepted result."""
        return EvaluationResult(is_acceptable=True, rejection_reasons=RejectionReasons())

    @staticmethod
    def rejected(reasons: RejectionReasons) -> "EvaluationResult":
        """Create a rejected result with detailed reasons."""
        return EvaluationResult(is_acceptable=False, rejection_reasons=reasons)
