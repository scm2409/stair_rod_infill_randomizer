"""Parameters for Pass-Through Evaluator."""

from railing_generator.domain.evaluators.evaluator_parameters import EvaluatorParameters


class PassThroughEvaluatorParameters(EvaluatorParameters):
    """
    Parameters for Pass-Through Evaluator.

    The Pass-Through Evaluator has no configurable parameters.
    It always returns a neutral fitness score and accepts all arrangements.
    This is the fastest evaluation option when quality optimization is not needed.
    """

    pass
