"""Base class for evaluator parameters."""

from abc import ABC

from pydantic import BaseModel


class EvaluatorParameters(BaseModel, ABC):
    """
    Abstract base class for evaluator parameters.

    All evaluator parameter classes must inherit from this base class.
    This provides a common interface for type checking and validation.
    """

    pass
