"""Base classes for infill generator parameters and defaults."""

from abc import ABC
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class InfillGeneratorDefaults(ABC):
    """
    Abstract base class for infill generator default values.

    Subclasses define default parameter values loaded from Hydra configuration.
    These are dataclasses (not Pydantic) because Hydra works with dataclasses.
    """

    pass


class InfillGeneratorParameters(BaseModel, ABC):
    """
    Abstract base class for infill generator runtime parameters.

    Subclasses define generator-specific parameters with Pydantic validation.
    These are Pydantic models for runtime validation and UI integration.
    """

    pass
