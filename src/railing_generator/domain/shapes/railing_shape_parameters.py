"""Base classes for railing shape parameters and defaults."""

from abc import ABC
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class RailingShapeDefaults(ABC):
    """
    Abstract base class for railing shape default values.

    Subclasses define default parameter values loaded from Hydra configuration.
    These are dataclasses (not Pydantic) because Hydra works with dataclasses.
    """

    pass


class RailingShapeParameters(BaseModel, ABC):
    """
    Abstract base class for railing shape runtime parameters.

    Subclasses define shape-specific parameters with Pydantic validation.
    These are Pydantic models for runtime validation and UI integration.
    """

    pass
