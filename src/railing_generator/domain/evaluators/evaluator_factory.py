"""Factory for creating evaluator instances from parameter objects."""

from railing_generator.domain.evaluators.evaluator import Evaluator
from railing_generator.domain.evaluators.evaluator_parameters import EvaluatorParameters
from railing_generator.domain.evaluators.passthrough_evaluator import PassThroughEvaluator
from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
    PassThroughEvaluatorParameters,
)
from railing_generator.domain.evaluators.quality_evaluator import QualityEvaluator
from railing_generator.domain.evaluators.quality_evaluator_parameters import (
    QualityEvaluatorParameters,
)


class EvaluatorFactory:
    """
    Factory for creating evaluator instances from parameter objects.

    This factory uses the discriminator field in EvaluatorParameters to
    automatically create the correct evaluator type. This works seamlessly
    with Pydantic's discriminated unions.

    Supported evaluator types:
        - PassThroughEvaluatorParameters: Creates PassThroughEvaluator
        - QualityEvaluatorParameters: Creates QualityEvaluator
        - Future: Custom evaluators

    Example:
        >>> params = PassThroughEvaluatorParameters()
        >>> evaluator = EvaluatorFactory.create_evaluator(params)
    """

    @staticmethod
    def create_evaluator(params: EvaluatorParameters) -> Evaluator:
        """
        Create an evaluator instance from parameter object.

        Uses the 'type' discriminator field to determine which evaluator to create.
        This works automatically with Pydantic's discriminated unions.

        Args:
            params: The evaluator parameters (with type discriminator)

        Returns:
            An evaluator instance of the appropriate type

        Raises:
            ValueError: If the parameter type is unknown
        """
        if isinstance(params, PassThroughEvaluatorParameters):
            return PassThroughEvaluator(params)
        elif isinstance(params, QualityEvaluatorParameters):
            return QualityEvaluator(params)

        # Future evaluator types will be added here

        raise ValueError(f"Unknown evaluator parameter type: {type(params).__name__}")
