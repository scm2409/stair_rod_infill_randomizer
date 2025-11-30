"""Central state model for the railing project application."""

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from railing_generator.domain.generation_progress import GenerationProgress
from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.shapes.railing_shape_parameters import RailingShapeParameters


class RailingProjectModel(QObject):
    """
    Central state model for the railing project application.

    This class stores all runtime state and emits signals when state changes.
    UI components observe this model and update themselves when signals are emitted.

    State includes:
    - Railing shape type and parameters
    - Current RailingFrame (immutable reference)
    - Infill generator type and parameters
    - Current RailingInfill (immutable reference)
    - Project file path and modified flag
    - UI state (rod annotation visibility, etc.)

    Signals use past tense naming to indicate state has changed.
    """

    # Signals for state changes (past tense naming)
    # IMPORTANT: PySide6 Signal type limitation
    # PySide6 Signal doesn't support Union types (e.g., RailingFrame | None).
    # We use 'object' type for signals that can emit None or specific types.
    # This is a PySide6 framework limitation, not a design choice.
    # Receivers should type-check the emitted value if needed.
    railing_shape_type_changed = Signal(str)  # Shape type selected
    railing_shape_parameters_changed = Signal(object)  # RailingShapeParameters | None
    railing_frame_updated = Signal(object)  # RailingFrame | None
    infill_generator_type_changed = Signal(str)  # Infill generator type selected
    infill_generator_parameters_changed = Signal(object)  # InfillGeneratorParameters | None
    railing_infill_updated = Signal(object)  # RailingInfill | None
    project_file_path_changed = Signal(object)  # Path | None
    project_modified_changed = Signal(bool)  # Dirty flag changed
    rod_annotation_visibility_changed = Signal(bool)  # Rod annotation toggled
    infill_layers_colored_by_layer_changed = Signal(bool)  # Infill color mode toggled
    generation_progress_updated = Signal(GenerationProgress)  # GenerationProgress (never None)

    def __init__(self) -> None:
        """Initialize the project model with default state."""
        super().__init__()

        # Railing shape state
        self._railing_shape_type: str | None = None
        self._railing_shape_parameters: RailingShapeParameters | None = None
        self._railing_frame: RailingFrame | None = None

        # Infill generator state
        self._infill_generator_type: str | None = None
        # TODO(Task 5.2): Add specific generator parameter types when generators are implemented
        self._infill_generator_parameters: InfillGeneratorParameters | None = None
        self._railing_infill: RailingInfill | None = None

        # Project state
        self._project_file_path: Path | None = None
        self._project_modified: bool = False

        # UI state
        self._rod_annotation_visible: bool = False
        self._infill_layers_colored_by_layer: bool = True  # Default: colored mode

        # Generation progress state
        self._generation_progress: GenerationProgress = GenerationProgress()

    # Property getters for all state fields

    @property
    def railing_shape_type(self) -> str | None:
        """Get the current railing shape type."""
        return self._railing_shape_type

    @property
    def railing_shape_parameters(self) -> RailingShapeParameters | None:
        """Get the current railing shape parameters."""
        return self._railing_shape_parameters

    @property
    def railing_frame(self) -> RailingFrame | None:
        """Get the current railing frame."""
        return self._railing_frame

    @property
    def infill_generator_type(self) -> str | None:
        """Get the current infill generator type."""
        return self._infill_generator_type

    @property
    def infill_generator_parameters(self) -> InfillGeneratorParameters | None:
        """Get the current infill generator parameters."""
        return self._infill_generator_parameters

    @property
    def railing_infill(self) -> RailingInfill | None:
        """Get the current railing infill."""
        return self._railing_infill

    @property
    def project_file_path(self) -> Path | None:
        """Get the current project file path."""
        return self._project_file_path

    @property
    def project_modified(self) -> bool:
        """Get whether the project has unsaved changes."""
        return self._project_modified

    @property
    def rod_annotation_visible(self) -> bool:
        """Get whether rod annotation is visible."""
        return self._rod_annotation_visible

    @property
    def infill_layers_colored_by_layer(self) -> bool:
        """Get whether infill layers are colored by layer."""
        return self._infill_layers_colored_by_layer

    @property
    def generation_progress(self) -> GenerationProgress:
        """Get the current generation progress data."""
        return self._generation_progress

    # State setter methods with signal emissions

    def set_railing_shape_type(self, shape_type: str) -> None:
        """
        Set the railing shape type.

        Clears the frame when shape type changes.

        Args:
            shape_type: The new shape type identifier
        """
        if self._railing_shape_type != shape_type:
            self._railing_shape_type = shape_type
            self.railing_shape_type_changed.emit(shape_type)

            # Clear frame when shape type changes
            self.set_railing_frame(None)

    def set_railing_shape_parameters(self, parameters: RailingShapeParameters) -> None:
        """
        Set the railing shape parameters.

        Marks project as modified.

        Args:
            parameters: The new shape parameters (RailingShapeParameters subclass)
        """
        self._railing_shape_parameters = parameters
        self._mark_modified()
        self.railing_shape_parameters_changed.emit(parameters)

    def set_railing_frame(self, frame: RailingFrame | None) -> None:
        """
        Set the railing frame.

        Clears infill when frame changes. Marks project as modified.

        Args:
            frame: The new railing frame, or None to clear
        """
        self._railing_frame = frame
        self._mark_modified()
        self.railing_frame_updated.emit(frame)

        # Clear infill when frame changes
        if self._railing_infill is not None:
            self.set_railing_infill(None)

    def set_infill_generator_type(self, infill_generator_type: str) -> None:
        """
        Set the infill generator type.

        Marks project as modified.

        Args:
            infill_generator_type: The new infill generator type identifier
        """
        if self._infill_generator_type != infill_generator_type:
            self._infill_generator_type = infill_generator_type
            self._mark_modified()
            self.infill_generator_type_changed.emit(infill_generator_type)

    def set_infill_generator_parameters(self, parameters: InfillGeneratorParameters) -> None:
        """
        Set the infill generator parameters.

        Marks project as modified.

        Args:
            parameters: The new infill generator parameters (InfillGeneratorParameters subclass)
        """
        self._infill_generator_parameters = parameters
        self._mark_modified()
        self.infill_generator_parameters_changed.emit(parameters)

    def set_railing_infill(self, infill: RailingInfill | None) -> None:
        """
        Set the railing infill.

        Marks project as modified.

        Args:
            infill: The new railing infill, or None to clear
        """
        self._railing_infill = infill
        self._mark_modified()
        self.railing_infill_updated.emit(infill)

    def set_project_file_path(self, file_path: Path | None) -> None:
        """
        Set the project file path.

        Args:
            file_path: The new file path, or None for unsaved project
        """
        self._project_file_path = file_path
        self.project_file_path_changed.emit(file_path)

    def mark_project_saved(self) -> None:
        """
        Mark the project as saved.

        Clears the modified flag and emits signal.
        """
        self._project_modified = False
        self.project_modified_changed.emit(False)

    def set_rod_annotation_visible(self, visible: bool) -> None:
        """
        Set the rod annotation visibility.

        Args:
            visible: Whether rod annotation should be visible
        """
        if self._rod_annotation_visible != visible:
            self._rod_annotation_visible = visible
            self.rod_annotation_visibility_changed.emit(visible)

    def set_infill_layers_colored_by_layer(self, colored: bool) -> None:
        """
        Set the infill layer color mode.

        Args:
            colored: True for colored mode (each layer distinct color),
                    False for monochrome mode (all layers same color)
        """
        if self._infill_layers_colored_by_layer != colored:
            self._infill_layers_colored_by_layer = colored
            self.infill_layers_colored_by_layer_changed.emit(colored)

    def toggle_infill_layers_colored_by_layer(self) -> None:
        """Toggle the infill layer color mode between colored and monochrome."""
        self.set_infill_layers_colored_by_layer(not self._infill_layers_colored_by_layer)

    def set_generation_progress(self, progress: GenerationProgress) -> None:
        """
        Set the generation progress data.

        Args:
            progress: GenerationProgress object with iteration, fitness, and elapsed time
        """
        self._generation_progress = progress
        self.generation_progress_updated.emit(progress)

    # Utility methods

    def reset_to_defaults(self) -> None:
        """
        Reset the model to default state.

        Clears all state and emits all signals.
        """
        # Clear shape state
        self._railing_shape_type = None
        self._railing_shape_parameters = None
        self._railing_frame = None

        # Clear infill generator state
        self._infill_generator_type = None
        self._infill_generator_parameters = None
        self._railing_infill = None

        # Clear project state
        self._project_file_path = None
        self._project_modified = False

        # Clear UI state
        self._rod_annotation_visible = False
        self._infill_layers_colored_by_layer = True  # Reset to default (colored mode)

        # Emit all signals
        self.railing_shape_type_changed.emit("")  # Empty string for "no selection"
        self.railing_shape_parameters_changed.emit(None)
        self.railing_frame_updated.emit(None)
        self.infill_generator_type_changed.emit("")
        self.infill_generator_parameters_changed.emit(None)
        self.railing_infill_updated.emit(None)
        self.project_file_path_changed.emit(None)
        self.project_modified_changed.emit(False)
        self.rod_annotation_visibility_changed.emit(False)
        self.infill_layers_colored_by_layer_changed.emit(True)

    def has_railing_frame(self) -> bool:
        """
        Check if a railing frame exists.

        Returns:
            True if frame exists, False otherwise
        """
        return self._railing_frame is not None

    def has_railing_infill(self) -> bool:
        """
        Check if a railing infill exists.

        Returns:
            True if infill exists, False otherwise
        """
        return self._railing_infill is not None

    # Private helper methods

    def _mark_modified(self) -> None:
        """Mark the project as modified if not already marked."""
        if not self._project_modified:
            self._project_modified = True
            self.project_modified_changed.emit(True)
