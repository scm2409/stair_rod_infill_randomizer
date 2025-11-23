"""Application controller for orchestrating workflows and updating the model."""

from PySide6.QtCore import QObject, QThread, Signal, Slot

from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.infill_generators.generator import Generator
from railing_generator.domain.infill_generators.generator_factory import GeneratorFactory
from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.shapes.railing_shape_factory import RailingShapeFactory
from railing_generator.domain.shapes.railing_shape_parameters import RailingShapeParameters


class GenerationWorker(QObject):
    """
    Worker object for running generation in a background thread.

    This worker is a simple wrapper that calls the generator's generate() method.
    The generator itself emits signals directly to the main thread via Qt's
    automatic queued connections (since generator lives in worker thread).

    Best Practice: We don't forward signals here. The generator's signals are
    connected in the main thread BEFORE the worker is moved to the thread.
    Qt automatically uses queued connections for cross-thread signals.
    """

    def __init__(
        self,
        generator: Generator,
        frame: RailingFrame,
        params: InfillGeneratorParameters,
    ):
        """
        Initialize the generation worker.

        Args:
            generator: The generator instance to run
            frame: The railing frame to generate infill for
            params: The generation parameters (includes nested evaluator params)
        """
        super().__init__()
        self.generator = generator
        self.frame = frame
        self.params = params

    @Slot()
    def run(self) -> None:
        """
        Run the generation in the background thread.

        This method is called when the thread starts.
        It simply calls the generator's generate() method.
        The generator emits signals directly (Qt handles thread safety).
        """
        try:
            # Generator creates its own evaluator from params
            self.generator.generate(self.frame, self.params)
        except Exception as e:
            # Emit failure signal from generator
            self.generator.generation_failed.emit(str(e))


class ApplicationController(QObject):
    """
    Application controller that orchestrates workflows and updates RailingProjectModel.

    This controller:
    - Creates domain objects (shapes, generators)
    - Orchestrates background threads for generation
    - Updates the model (never updates UI directly)
    - Handles serialization/deserialization for save/load

    The controller updates the model via setter methods, and the model emits signals
    to notify UI observers. This maintains clear separation between application logic
    and presentation.

    Signals:
        generation_started: Emitted when background generation starts
    """

    generation_started = Signal(object)  # Generator instance

    def __init__(self, project_model: RailingProjectModel):
        """
        Initialize the application controller.

        Args:
            project_model: The central state model to update
        """
        super().__init__()
        self.project_model = project_model
        self._generation_thread: QThread | None = None
        self._generation_worker: GenerationWorker | None = None
        self._current_generator: Generator | None = None

    def create_new_project(self) -> None:
        """
        Create a new project by resetting the model to default state.

        This clears all state and emits signals to notify observers.
        """
        self.project_model.reset_to_defaults()

    def update_railing_shape(self, shape_type: str, parameters: RailingShapeParameters) -> None:
        """
        Update the railing shape by generating a new frame.

        This method:
        1. Creates a RailingShape instance from the type and parameters
        2. Generates the RailingFrame
        3. Updates the model with the new frame

        The model will emit signals to notify observers (e.g., viewport).

        Args:
            shape_type: The shape type identifier (e.g., "staircase")
            parameters: The validated shape parameters

        Raises:
            ValueError: If the shape type is unknown or parameters are invalid
        """
        # Update model with shape type and parameters
        self.project_model.set_railing_shape_type(shape_type)
        self.project_model.set_railing_shape_parameters(parameters)

        # Create shape instance and generate frame
        shape = RailingShapeFactory.create_shape(shape_type, parameters)
        frame = shape.generate_frame()

        # Update model with the generated frame
        self.project_model.set_railing_frame(frame)

    def generate_infill(self, generator_type: str, parameters: InfillGeneratorParameters) -> None:
        """
        Generate infill for the current railing frame in a background thread.

        This method:
        1. Validates that a frame exists
        2. Creates a Generator instance from the type and parameters
        3. Starts background generation in a QThread
        4. Emits generation_started signal with the generator instance

        The generator will emit signals during generation:
        - progress_updated: Real-time progress metrics
        - best_result_updated: New best result found
        - generation_completed: Generation finished successfully
        - generation_failed: Generation failed with error

        The UI should connect to these signals to show progress and update the viewport.

        Threading Architecture:
        - Generator is created in main thread
        - Worker wraps the generator and is moved to worker thread
        - Generator signals are connected in main thread BEFORE thread starts
        - Qt automatically uses queued connections for cross-thread signals
        - This avoids thread affinity issues and signal connection problems

        Args:
            generator_type: The generator type identifier (e.g., "random")
            parameters: The validated generator parameters

        Raises:
            ValueError: If no frame exists, generator type is unknown, or parameters are invalid
            RuntimeError: If a generation is already in progress
        """
        # Validate that a frame exists
        if not self.project_model.has_railing_frame():
            raise ValueError("Cannot generate infill: no railing frame exists")

        # Check if generation is already in progress
        if self._generation_thread is not None and self._generation_thread.isRunning():
            raise RuntimeError("Generation already in progress")

        # Clear current infill before starting new generation
        self.project_model.set_railing_infill(None)

        # Get the current frame
        frame = self.project_model.railing_frame

        # Type narrowing: we know frame is not None because has_railing_frame() returned True
        assert frame is not None, "Frame should not be None after has_railing_frame() check"

        # Update model with generator type and parameters
        self.project_model.set_infill_generator_type(generator_type)
        self.project_model.set_infill_generator_parameters(parameters)

        # Create generator instance (in main thread)
        # Generator will create its own evaluator from nested parameters
        generator = GeneratorFactory.create_generator(generator_type, parameters)
        self._current_generator = generator

        # Create worker and thread
        self._generation_thread = QThread()
        self._generation_worker = GenerationWorker(generator, frame, parameters)

        # IMPORTANT: Move worker to thread BEFORE connecting signals
        # This ensures proper thread affinity for the worker
        self._generation_worker.moveToThread(self._generation_thread)

        # Connect generator signals to controller for model updates
        # These connections are made in the main thread, Qt will automatically
        # use queued connections since generator will be in worker thread
        generator.generation_completed.connect(self._on_generation_completed)

        # Connect thread lifecycle signals
        self._generation_thread.started.connect(self._generation_worker.run)
        generator.generation_completed.connect(self._generation_thread.quit)
        generator.generation_failed.connect(self._generation_thread.quit)
        self._generation_thread.finished.connect(self._cleanup_generation_thread)

        # Start the thread
        self._generation_thread.start()

        # Emit signal to notify UI (e.g., to show progress dialog)
        # UI will connect to generator signals for progress updates
        self.generation_started.emit(generator)

    def _on_generation_completed(self, infill: object) -> None:
        """
        Handle generation completion by updating the model.

        Args:
            infill: The generated infill result (RailingInfill)
        """
        # Verify infill has required attributes (duck typing approach)
        if not hasattr(infill, "rods"):
            raise TypeError("Infill result missing required 'rods' attribute")

        # Type narrowing: we trust this is RailingInfill from the signal
        # Cast for type checker (runtime check done above)
        from typing import cast

        typed_infill = cast(RailingInfill, infill)
        self.project_model.set_railing_infill(typed_infill)

    def _cleanup_generation_thread(self) -> None:
        """Clean up the generation thread after it finishes."""
        if self._generation_thread is not None:
            self._generation_thread.deleteLater()
            self._generation_thread = None
        if self._generation_worker is not None:
            self._generation_worker.deleteLater()
            self._generation_worker = None

    def cancel_generation(self) -> None:
        """
        Cancel the ongoing generation.

        This sets the cancellation flag on the generator, which will
        cause it to stop at the next iteration and return the best result found.
        """
        if self._current_generator is not None:
            self._current_generator.cancel()
