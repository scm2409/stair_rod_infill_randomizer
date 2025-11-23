"""Pass-Through Evaluator implementation."""

from railing_generator.domain.evaluators.evaluator import Evaluator
from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
    PassThroughEvaluatorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill


class PassThroughEvaluator(Evaluator):
    """
    Pass-Through Evaluator that accepts all arrangements without scoring.

    This evaluator provides the fastest evaluation by always returning
    a neutral fitness score and accepting all valid arrangements.
    It's useful for quick previews or when speed is priority over quality.

    Behavior:
        - evaluate(): Always returns 1.0 (neutral score)
        - is_acceptable(): Always returns True (accepts all arrangements)
    """

    def __init__(self, params: PassThroughEvaluatorParameters) -> None:
        """
        Initialize the Pass-Through Evaluator.

        Args:
            params: Evaluator parameters (empty for Pass-Through)
        """
        self.params = params

    def evaluate(self, infill: RailingInfill, frame: RailingFrame) -> float:
        """
        Return neutral fitness score without evaluation.

        Args:
            infill: The infill arrangement (not used)
            frame: The railing frame (not used)

        Returns:
            Always returns 1.0 (neutral score)
        """
        return 1.0

    def is_acceptable(self, infill: RailingInfill, frame: RailingFrame) -> bool:
        """
        Accept all arrangements without checking.

        Args:
            infill: The infill arrangement (not used)
            frame: The railing frame (not used)

        Returns:
            Always returns True (accepts all arrangements)
        """
        return True
