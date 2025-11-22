"""Base class for infill generators."""

from abc import ABCMeta, abstractmethod

from PySide6.QtCore import QObject, Signal

from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill


class QObjectABCMeta(type(QObject), ABCMeta):  # type: ignore[misc]
    """Metaclass that combines QObject and ABC metaclasses."""

    pass


class Generator(QObject, metaclass=QObjectABCMeta):
    """
    Abstract base class for all infill generators.

    Generators create infill rod arrangements within a railing frame boundary.
    They emit signals during generation for progress updates and results.

    Subclasses must define:
        PARAMETER_TYPE: The specific InfillGeneratorParameters subclass this generator uses

    Signals:
        progress_updated: Emitted during generation with progress info dict
        best_result_updated: Emitted when a better result is found (RailingInfill)
        generation_completed: Emitted when generation completes successfully (RailingInfill)
        generation_failed: Emitted when generation fails (error message string)
    """

    # Subclasses must define their parameter type
    PARAMETER_TYPE: type[InfillGeneratorParameters]

    # Signals for generation progress and results
    progress_updated = Signal(
        dict
    )  # {"iteration": int, "best_fitness": float, "elapsed_sec": float}
    best_result_updated = Signal(object)  # RailingInfill
    generation_completed = Signal(object)  # RailingInfill
    generation_failed = Signal(str)  # error message

    def __init__(self) -> None:
        """Initialize the generator."""
        super().__init__()
        self._cancelled = False

    @abstractmethod
    def generate(self, frame: RailingFrame, params: InfillGeneratorParameters) -> RailingInfill:
        """
        Generate infill arrangement within the given frame.

        This method should emit signals during generation:
        - progress_updated: For progress information
        - best_result_updated: When a better result is found
        - generation_completed: When generation succeeds
        - generation_failed: When generation fails

        Args:
            frame: The railing frame defining the boundary
            params: Generator-specific parameters (subclass of InfillGeneratorParameters)

        Returns:
            RailingInfill containing the generated rods and metadata

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If generation fails
        """
        pass

    def cancel(self) -> None:
        """Request cancellation of ongoing generation."""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled

    def reset_cancellation(self) -> None:
        """Reset the cancellation flag for a new generation."""
        self._cancelled = False
