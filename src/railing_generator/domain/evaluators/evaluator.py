"""Base class for evaluators."""

from abc import ABC, abstractmethod

from railing_generator.domain.evaluators.evaluation_result import EvaluationResult
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill


class Evaluator(ABC):
    """
    Abstract base class for all evaluators.

    Evaluators assess the quality of infill arrangements and determine
    whether they meet acceptance criteria. They provide fitness scores
    for optimization and detailed acceptance checks for validation.

    Subclasses must implement:
        - evaluate(): Calculate fitness score for an arrangement
        - check_acceptance(): Check if arrangement meets minimum criteria with detailed reason
    """

    @abstractmethod
    def evaluate(self, infill: RailingInfill, frame: RailingFrame) -> float:
        """
        Evaluate the quality of an infill arrangement.

        Args:
            infill: The infill arrangement to evaluate
            frame: The railing frame containing the infill

        Returns:
            Fitness score where higher values indicate better quality.
            Typical range is 0.0 to 1.0, but implementations may use
            different scales.
        """
        pass

    @abstractmethod
    def check_acceptance(self, infill: RailingInfill, frame: RailingFrame) -> EvaluationResult:
        """
        Check if an infill arrangement meets minimum acceptance criteria.

        Args:
            infill: The infill arrangement to check
            frame: The railing frame containing the infill

        Returns:
            EvaluationResult with acceptance status and rejection reason (if rejected)
        """
        pass

    def is_acceptable(self, infill: RailingInfill, frame: RailingFrame) -> bool:
        """
        Check if an infill arrangement is acceptable (convenience method).

        This is a convenience wrapper around check_acceptance() that only
        returns the boolean status. Use check_acceptance() directly if you
        need the rejection reason.

        Args:
            infill: The infill arrangement to check
            frame: The railing frame containing the infill

        Returns:
            True if the arrangement is acceptable, False otherwise
        """
        return self.check_acceptance(infill, frame).is_acceptable
