"""Application controller for orchestrating workflows and updating the model."""

import csv
import io
import logging
import zipfile
from pathlib import Path
from typing import Any, cast

from PySide6.QtCore import QObject, QThread, Signal, Slot

from railing_generator.application.persistable_project_state import (
    GeneratorParametersUnion,
    PersistedFrame,
    PersistedInfill,
    PersistableProjectState,
    ShapeParametersUnion,
    UIState,
)
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.infill_generators.generator import Generator
from railing_generator.domain.infill_generators.generator_factory import GeneratorFactory
from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod
from railing_generator.domain.shapes.railing_shape_factory import RailingShapeFactory
from railing_generator.domain.shapes.railing_shape_parameters import RailingShapeParameters

logger = logging.getLogger(__name__)


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

    # =========================================================================
    # Project Persistence (Save/Load)
    # =========================================================================

    def save_project(self, file_path: Path, png_data: bytes | None = None) -> None:
        """
        Save the current project state to a .rig.zip archive.

        The archive contains:
        - project.json: Complete typed project state (single file)
        - preview.png: Viewport screenshot (if provided)
        - frame_bom.csv: Frame parts table (if frame exists)
        - infill_bom.csv: Infill parts table (if infill exists)

        Args:
            file_path: Path to save the .rig.zip file
            png_data: Optional PNG image data for preview

        Raises:
            ValueError: If no frame exists (nothing to save)
        """
        if not self.project_model.has_railing_frame():
            raise ValueError("Cannot save project: no railing frame exists")

        # Build typed project state
        state = self._build_project_state()

        # Create ZIP archive
        with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Write project.json (single typed file)
            zf.writestr("project.json", state.model_dump_json(indent=2))

            # Write preview.png (if provided)
            if png_data is not None:
                zf.writestr("preview.png", png_data)

            # Write BOM CSV files
            frame = self.project_model.railing_frame
            if frame is not None:
                bom_entries = [rod.to_bom_entry(i + 1) for i, rod in enumerate(frame.rods)]
                zf.writestr("frame_bom.csv", self._generate_bom_csv(bom_entries))

            infill = self.project_model.railing_infill
            if infill is not None:
                bom_entries = [rod.to_bom_entry(i + 1) for i, rod in enumerate(infill.rods)]
                zf.writestr("infill_bom.csv", self._generate_bom_csv(bom_entries))

        # Update model with file path and mark as saved
        self.project_model.set_project_file_path(file_path)
        self.project_model.mark_project_saved()

        logger.info(f"Project saved to {file_path}")

    def load_project(self, file_path: Path) -> None:
        """
        Load a project from a .rig.zip archive.

        Restores all parameters, frame geometry, and infill geometry.
        Updates the model state and emits signals to notify observers.

        Args:
            file_path: Path to the .rig.zip file to load

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the archive is invalid or missing required data
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Project file not found: {file_path}")

        # Read ZIP archive
        with zipfile.ZipFile(file_path, "r") as zf:
            # Read project.json (new format) or parameters.json (legacy)
            if "project.json" in zf.namelist():
                project_json = zf.read("project.json").decode("utf-8")
                state = PersistableProjectState.model_validate_json(project_json)
            elif "parameters.json" in zf.namelist():
                # Legacy format support - convert to new format
                state = self._load_legacy_format(zf)
            else:
                raise ValueError("Invalid project file: missing project.json")

        # Apply state to model
        self._apply_project_state(state)

        # Update model with file path and mark as saved
        self.project_model.set_project_file_path(file_path)
        self.project_model.mark_project_saved()

        logger.info(f"Project loaded from {file_path}")

    def _build_project_state(self) -> PersistableProjectState:
        """
        Build a typed PersistableProjectState from the current model.

        Returns:
            PersistableProjectState containing all persistable data
        """
        # Build frame if exists
        frame: PersistedFrame | None = None
        if self.project_model.railing_frame is not None:
            frame = PersistedFrame(rods=self.project_model.railing_frame.rods)

        # Build infill if exists
        infill: PersistedInfill | None = None
        if self.project_model.railing_infill is not None:
            src_infill = self.project_model.railing_infill
            infill = PersistedInfill(
                rods=src_infill.rods,
                fitness_score=src_infill.fitness_score,
                iteration_count=src_infill.iteration_count,
                duration_sec=src_infill.duration_sec,
                anchor_points=src_infill.anchor_points,
                is_complete=src_infill.is_complete,
            )

        # Build UI state
        ui_state = UIState(
            rod_annotation_visible=self.project_model.rod_annotation_visible,
            infill_layers_colored_by_layer=self.project_model.infill_layers_colored_by_layer,
        )

        # Cast parameters to union types for Pydantic
        shape_params: ShapeParametersUnion | None = None
        if self.project_model.railing_shape_parameters is not None:
            shape_params = cast(ShapeParametersUnion, self.project_model.railing_shape_parameters)

        gen_params: GeneratorParametersUnion | None = None
        if self.project_model.infill_generator_parameters is not None:
            gen_params = cast(
                GeneratorParametersUnion, self.project_model.infill_generator_parameters
            )

        return PersistableProjectState(
            shape_type=self.project_model.railing_shape_type,
            shape_parameters=shape_params,
            generator_type=self.project_model.infill_generator_type,
            generator_parameters=gen_params,
            frame=frame,
            infill=infill,
            ui_state=ui_state,
        )

    def _apply_project_state(self, state: PersistableProjectState) -> None:
        """
        Apply a PersistableProjectState to the model.

        Args:
            state: The typed project state to apply
        """
        # Reset model first
        self.project_model.reset_to_defaults()

        # Restore shape type and parameters
        if state.shape_type and state.shape_parameters:
            self.project_model.set_railing_shape_type(state.shape_type)
            self.project_model.set_railing_shape_parameters(state.shape_parameters)

        # Restore generator type and parameters
        if state.generator_type:
            self.project_model.set_infill_generator_type(state.generator_type)
        if state.generator_parameters:
            self.project_model.set_infill_generator_parameters(state.generator_parameters)

        # Restore UI state
        self.project_model.set_rod_annotation_visible(state.ui_state.rod_annotation_visible)
        self.project_model.set_infill_layers_colored_by_layer(
            state.ui_state.infill_layers_colored_by_layer
        )

        # Restore frame geometry
        if state.frame is not None:
            frame = RailingFrame(rods=state.frame.rods)
            # Bypass the normal setter to avoid marking as modified
            self.project_model._railing_frame = frame
            self.project_model.railing_frame_updated.emit(frame)

        # Restore infill geometry
        if state.infill is not None:
            infill = RailingInfill(
                rods=state.infill.rods,
                fitness_score=state.infill.fitness_score,
                iteration_count=state.infill.iteration_count,
                duration_sec=state.infill.duration_sec,
                is_complete=state.infill.is_complete,
                anchor_points=state.infill.anchor_points,
            )
            # Bypass the normal setter to avoid marking as modified
            self.project_model._railing_infill = infill
            self.project_model.railing_infill_updated.emit(infill)

    def _load_legacy_format(self, zf: zipfile.ZipFile) -> PersistableProjectState:
        """
        Load legacy format (parameters.json + separate geometry files).

        Args:
            zf: Open ZipFile to read from

        Returns:
            PersistableProjectState converted from legacy format
        """
        import json
        from typing import Any

        from shapely.geometry import LineString

        from railing_generator.domain.anchor_point import AnchorPoint
        from railing_generator.domain.infill_generators.random_generator_parameters import (
            RandomGeneratorParameters,
        )
        from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
            RandomGeneratorParametersV2,
        )
        from railing_generator.domain.shapes.rectangular_railing_shape import (
            RectangularRailingShapeParameters,
        )
        from railing_generator.domain.shapes.staircase_railing_shape import (
            StaircaseRailingShapeParameters,
        )

        # Read parameters.json
        params_json = zf.read("parameters.json").decode("utf-8")
        parameters: dict[str, Any] = json.loads(params_json)

        # Parse shape parameters
        shape_type = parameters.get("shape_type")
        shape_params_dict = parameters.get("shape_parameters", {})
        shape_params: ShapeParametersUnion | None = None
        if shape_type == "staircase" and shape_params_dict:
            shape_params = StaircaseRailingShapeParameters(**shape_params_dict)
        elif shape_type == "rectangular" and shape_params_dict:
            shape_params = RectangularRailingShapeParameters(**shape_params_dict)

        # Parse generator parameters
        generator_type = parameters.get("generator_type")
        gen_params_dict = parameters.get("generator_parameters", {})
        gen_params: GeneratorParametersUnion | None = None
        if generator_type == "random" and gen_params_dict:
            gen_params = RandomGeneratorParameters(**gen_params_dict)
        elif generator_type == "random_v2" and gen_params_dict:
            gen_params = RandomGeneratorParametersV2(**gen_params_dict)

        # Parse UI state
        ui_state_dict = parameters.get("ui_state", {})
        ui_state = UIState(
            rod_annotation_visible=ui_state_dict.get("rod_annotation_visible", False),
            infill_layers_colored_by_layer=ui_state_dict.get(
                "infill_layers_colored_by_layer", True
            ),
        )

        # Parse frame geometry
        frame: PersistedFrame | None = None
        if "frame_geometry.json" in zf.namelist():
            frame_json = zf.read("frame_geometry.json").decode("utf-8")
            frame_data: list[dict[str, Any]] = json.loads(frame_json)
            frame_rods = self._parse_legacy_rods(frame_data)
            frame = PersistedFrame(rods=frame_rods)

        # Parse infill geometry
        infill: PersistedInfill | None = None
        if "infill_geometry.json" in zf.namelist():
            infill_json = zf.read("infill_geometry.json").decode("utf-8")
            infill_data: dict[str, Any] = json.loads(infill_json)
            infill_rods = self._parse_legacy_rods(infill_data.get("rods", []))

            # Parse anchor points
            anchor_points: list[AnchorPoint] | None = None
            if infill_data.get("anchor_points"):
                anchor_points = [AnchorPoint(**ap) for ap in infill_data["anchor_points"]]

            infill = PersistedInfill(
                rods=infill_rods,
                fitness_score=infill_data.get("fitness_score"),
                iteration_count=infill_data.get("iteration_count"),
                duration_sec=infill_data.get("duration_sec"),
                is_complete=infill_data.get("is_complete", True),
                anchor_points=anchor_points,
            )

        return PersistableProjectState(
            shape_type=shape_type,
            shape_parameters=shape_params,
            generator_type=generator_type,
            generator_parameters=gen_params,
            frame=frame,
            infill=infill,
            ui_state=ui_state,
        )

    def _parse_legacy_rods(self, rod_data: list[dict[str, Any]]) -> list[Rod]:
        """
        Parse rods from legacy format.

        Args:
            rod_data: List of rod dictionaries from legacy format

        Returns:
            List of Rod objects
        """
        from typing import Any

        from shapely.geometry import LineString

        rods = []
        for data in rod_data:
            # Extract geometry coordinates
            coords = data.get("geometry", [])

            # Remove computed fields
            clean_data = {
                k: v
                for k, v in data.items()
                if k
                not in {
                    "geometry",
                    "length_cm",
                    "weight_kg",
                    "start_point",
                    "end_point",
                    "angle_from_vertical_deg",
                }
            }

            # Create Rod with geometry
            rod = Rod(geometry=LineString(coords), **clean_data)
            rods.append(rod)

        return rods

    def _generate_bom_csv(self, bom_entries: list[dict[str, Any]]) -> str:
        """
        Generate CSV content from BOM entries.

        Args:
            bom_entries: List of BOM entry dictionaries

        Returns:
            CSV content as string
        """
        if not bom_entries:
            return ""

        output = io.StringIO()
        fieldnames = ["id", "length_cm", "start_cut_angle_deg", "end_cut_angle_deg", "weight_kg"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(bom_entries)

        return output.getvalue()
