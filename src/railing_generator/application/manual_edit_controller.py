"""Manual edit controller for interactive rod editing."""

from datetime import datetime

from PySide6.QtCore import QObject, Signal
from shapely.geometry import LineString, Point

from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.anchor_point import AnchorPoint
from railing_generator.domain.anchor_point_finder import AnchorPointFinder
from railing_generator.domain.fitness_update import FitnessUpdate
from railing_generator.domain.infill_edit_operation import InfillEditOperation
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod


class ManualEditController(QObject):
    """
    Controls manual rod editing operations.

    This controller manages the selection state for manual rod editing
    and provides methods for selecting anchor points and clearing selections.

    The controller observes the RailingProjectModel and emits signals
    when selection state changes.

    Attributes:
        project_model: Reference to the central project model
        anchor_finder: AnchorPointFinder for spatial searches
    """

    # Signals
    selection_changed = Signal(object)  # AnchorPoint | None
    fitness_scores_updated = Signal(FitnessUpdate)
    undo_available_changed = Signal(bool)
    redo_available_changed = Signal(bool)

    # Default max history size
    DEFAULT_MAX_HISTORY_SIZE = 50

    def __init__(
        self,
        project_model: RailingProjectModel,
        search_radius_cm: float = 10.0,
        max_history_size: int = DEFAULT_MAX_HISTORY_SIZE,
    ) -> None:
        """
        Initialize the manual edit controller.

        Args:
            project_model: Reference to the central project model
            search_radius_cm: Search radius for anchor point finding (default: 10.0)
            max_history_size: Maximum number of operations in undo history (default: 50)
        """
        super().__init__()
        self._project_model = project_model
        self._anchor_finder = AnchorPointFinder(search_radius_cm=search_radius_cm)
        self._max_history_size = max_history_size

        # Selection state
        self._selected_anchor: AnchorPoint | None = None
        self._selected_rod_index: int | None = None

        # Undo/redo history
        self._undo_stack: list[InfillEditOperation] = []
        self._redo_stack: list[InfillEditOperation] = []

    @property
    def project_model(self) -> RailingProjectModel:
        """Get the project model reference."""
        return self._project_model

    @property
    def anchor_finder(self) -> AnchorPointFinder:
        """Get the anchor point finder."""
        return self._anchor_finder

    @property
    def selected_anchor(self) -> AnchorPoint | None:
        """Get the currently selected anchor point."""
        return self._selected_anchor

    @property
    def selected_rod_index(self) -> int | None:
        """Get the index of the rod connected to the selected anchor."""
        return self._selected_rod_index

    @property
    def has_selection(self) -> bool:
        """Check if an anchor point is currently selected."""
        return self._selected_anchor is not None

    def select_anchor_at(self, position: Point) -> bool:
        """
        Select a connected anchor point near the given position.

        Searches for the nearest connected (used) anchor point within the
        search radius and selects it if found. This anchor identifies
        which rod endpoint will be moved during reconnection.

        Args:
            position: Shapely Point of the search center

        Returns:
            True if an anchor was selected, False otherwise
        """
        # Get anchor points from current infill
        infill = self._project_model.railing_infill
        if infill is None or infill.anchor_points is None:
            self.clear_selection()
            return False

        # Find nearest connected anchor
        anchor = self._find_nearest_connected(position, infill.anchor_points)

        if anchor is None:
            # No anchor found within radius - don't change selection
            return False

        # Find which rod this anchor is connected to
        rod_index = self._find_rod_index_for_anchor(anchor)
        if rod_index is None:
            # Anchor marked as used but no rod found - inconsistent state
            return False

        # Update selection state
        self._selected_anchor = anchor
        self._selected_rod_index = rod_index
        self.selection_changed.emit(anchor)
        return True

    def _find_nearest_connected(
        self,
        position: Point,
        anchor_points: list[AnchorPoint],
    ) -> AnchorPoint | None:
        """
        Find the nearest connected (used) anchor point within search radius.

        Args:
            position: Shapely Point of the search center
            anchor_points: List of all anchor points

        Returns:
            Nearest connected anchor point, or None if none found
        """
        nearest: AnchorPoint | None = None
        nearest_distance: float = float("inf")

        for anchor in anchor_points:
            # Only consider connected (used) anchors
            if not anchor.used:
                continue

            # Calculate Euclidean distance using Shapely
            distance = position.distance(anchor.position)

            # Check if within search radius and closer than current nearest
            if distance <= self._anchor_finder.search_radius_cm and distance < nearest_distance:
                nearest = anchor
                nearest_distance = distance

        return nearest

    def clear_selection(self) -> None:
        """Clear the current anchor selection."""
        if self._selected_anchor is not None:
            self._selected_anchor = None
            self._selected_rod_index = None
            self.selection_changed.emit(None)

    def _find_rod_index_for_anchor(self, anchor: AnchorPoint) -> int | None:
        """
        Find the index of the rod connected to the given anchor.

        Args:
            anchor: The anchor point to search for

        Returns:
            Index of the connected rod, or None if not connected
        """
        infill = self._project_model.railing_infill
        if infill is None:
            return None

        # Search through rods to find one that has this anchor as an endpoint
        for i, rod in enumerate(infill.rods):
            if anchor.position.equals_exact(rod.start_point, tolerance=0.001):
                return i
            if anchor.position.equals_exact(rod.end_point, tolerance=0.001):
                return i

        return None

    # Undo/redo properties

    @property
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0

    @property
    def undo_stack_size(self) -> int:
        """Get the current size of the undo stack."""
        return len(self._undo_stack)

    @property
    def redo_stack_size(self) -> int:
        """Get the current size of the redo stack."""
        return len(self._redo_stack)

    # Rod reconnection

    def reconnect_to_anchor_at(self, position: Point) -> bool:
        """
        Reconnect the selected rod endpoint to an anchor near the position.

        This method:
        1. Finds the nearest unconnected anchor at the target position
        2. Creates a new rod geometry connecting to the target anchor
        3. Updates anchor point states (used flags, layer assignment)
        4. Creates an InfillEditOperation and pushes to undo stack
        5. Updates the project model with the new infill

        Args:
            position: Shapely Point of the target position

        Returns:
            True if reconnection was successful, False otherwise
        """
        # Validate preconditions
        if self._selected_anchor is None or self._selected_rod_index is None:
            return False

        infill = self._project_model.railing_infill
        if infill is None or infill.anchor_points is None:
            return False

        if self._selected_rod_index >= len(infill.rods):
            return False

        # Find target anchor
        target_anchor = self._anchor_finder.find_nearest_unconnected(position, infill.anchor_points)
        if target_anchor is None:
            return False

        # Get the source anchor index
        source_anchor_index = self._find_anchor_index(self._selected_anchor, infill.anchor_points)
        target_anchor_index = self._find_anchor_index(target_anchor, infill.anchor_points)
        if source_anchor_index is None or target_anchor_index is None:
            return False

        # Get the rod to modify
        rod = infill.rods[self._selected_rod_index]

        # Determine which endpoint to move (start or end)
        is_start_endpoint = self._selected_anchor.position.equals_exact(
            rod.start_point, tolerance=0.001
        )

        # Create new rod geometry
        if is_start_endpoint:
            # Move start point to target anchor
            new_geometry = LineString(
                [target_anchor.position.coords[0], (rod.end_point.x, rod.end_point.y)]
            )
        else:
            # Move end point to target anchor
            new_geometry = LineString(
                [(rod.start_point.x, rod.start_point.y), target_anchor.position.coords[0]]
            )

        # Create new rod with updated geometry
        new_rod = Rod(
            geometry=new_geometry,
            start_cut_angle_deg=rod.start_cut_angle_deg,
            end_cut_angle_deg=rod.end_cut_angle_deg,
            weight_kg_m=rod.weight_kg_m,
            layer=rod.layer,
        )

        # Create new rods list with the modified rod
        new_rods = list(infill.rods)
        new_rods[self._selected_rod_index] = new_rod

        # Update anchor points
        new_anchor_points = self._update_anchor_points(
            infill.anchor_points,
            source_anchor_index,
            target_anchor_index,
            rod.layer,
        )

        # Calculate new fitness score and acceptability using current evaluator
        new_fitness_score, is_acceptable = self._evaluate_infill(new_rods, new_anchor_points)

        # Create new infill with calculated fitness score
        new_infill = RailingInfill(
            rods=new_rods,
            fitness_score=new_fitness_score,
            iteration_count=infill.iteration_count,
            duration_sec=infill.duration_sec,
            anchor_points=new_anchor_points,
            is_complete=infill.is_complete,
        )

        # Create edit operation for undo
        operation = InfillEditOperation(
            previous_infill=infill,
            new_infill=new_infill,
            previous_fitness_score=infill.fitness_score,
            new_fitness_score=new_fitness_score,
            source_anchor_index=source_anchor_index,
            target_anchor_index=target_anchor_index,
            rod_index=self._selected_rod_index,
            timestamp=datetime.now(),
        )

        # Push to undo stack
        self._push_to_undo_stack(operation)

        # Update project model
        self._project_model.set_railing_infill(new_infill)

        # Emit fitness scores signal
        self.fitness_scores_updated.emit(
            FitnessUpdate(
                old_score=infill.fitness_score,
                new_score=new_fitness_score,
                is_acceptable=is_acceptable,
            )
        )

        # Clear selection
        self.clear_selection()

        return True

    def _find_anchor_index(
        self, anchor: AnchorPoint, anchor_points: list[AnchorPoint]
    ) -> int | None:
        """Find the index of an anchor in the anchor points list."""
        for i, ap in enumerate(anchor_points):
            if ap.position.equals_exact(anchor.position, tolerance=0.001):
                return i
        return None

    def _update_anchor_points(
        self,
        anchor_points: list[AnchorPoint],
        source_index: int,
        target_index: int,
        layer: int,
    ) -> list[AnchorPoint]:
        """
        Update anchor points after a reconnection.

        Args:
            anchor_points: Original anchor points list
            source_index: Index of the source anchor (to mark as unused)
            target_index: Index of the target anchor (to mark as used)
            layer: Layer to assign to the target anchor

        Returns:
            New list of anchor points with updated states
        """
        new_anchors: list[AnchorPoint] = []
        for i, ap in enumerate(anchor_points):
            if i == source_index:
                # Mark source as unused
                new_anchors.append(
                    AnchorPoint(
                        position=ap.position,
                        frame_segment_index=ap.frame_segment_index,
                        is_vertical_segment=ap.is_vertical_segment,
                        frame_segment_angle_deg=ap.frame_segment_angle_deg,
                        layer=ap.layer,
                        used=False,
                    )
                )
            elif i == target_index:
                # Mark target as used and assign layer
                new_anchors.append(
                    AnchorPoint(
                        position=ap.position,
                        frame_segment_index=ap.frame_segment_index,
                        is_vertical_segment=ap.is_vertical_segment,
                        frame_segment_angle_deg=ap.frame_segment_angle_deg,
                        layer=layer,
                        used=True,
                    )
                )
            else:
                new_anchors.append(ap)
        return new_anchors

    def _evaluate_infill(
        self,
        rods: list[Rod],
        anchor_points: list[AnchorPoint],
    ) -> tuple[float | None, bool | None]:
        """
        Evaluate the infill using the current evaluator.

        Gets the evaluator from the current generator parameters and runs it
        on the modified infill to calculate the new fitness score and check
        acceptability.

        Args:
            rods: List of rods in the infill
            anchor_points: List of anchor points

        Returns:
            Tuple of (fitness_score, is_acceptable), both None if no evaluator configured
        """
        from railing_generator.domain.evaluators.evaluator_factory import EvaluatorFactory
        from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
            RandomGeneratorParametersV2,
        )

        # Get current generator parameters
        gen_params = self._project_model.infill_generator_parameters
        if gen_params is None:
            return None, None

        # Check if it's a V2 generator with evaluator
        if not isinstance(gen_params, RandomGeneratorParametersV2):
            return None, None

        # Get the frame for evaluation
        frame = self._project_model.railing_frame
        if frame is None:
            return None, None

        # Create evaluator from parameters
        try:
            evaluator = EvaluatorFactory.create_evaluator(gen_params.evaluator)
        except (ValueError, AttributeError):
            return None, None

        # Create temporary infill for evaluation
        temp_infill = RailingInfill(
            rods=rods,
            fitness_score=None,
            anchor_points=anchor_points,
            is_complete=True,
        )

        # Run evaluator
        try:
            fitness_score = evaluator.evaluate(temp_infill, frame)
            is_acceptable = evaluator.is_acceptable(temp_infill, frame)

            # Also check for same-layer crossings (not covered by evaluator)
            if is_acceptable and self._has_same_layer_crossings(rods):
                is_acceptable = False

            return fitness_score, is_acceptable
        except Exception:
            return None, None

    def _has_same_layer_crossings(self, rods: list[Rod]) -> bool:
        """
        Check if any rods in the same layer cross each other.

        Args:
            rods: List of rods to check

        Returns:
            True if there are same-layer crossings, False otherwise
        """
        # Group rods by layer
        rods_by_layer: dict[int, list[Rod]] = {}
        for rod in rods:
            if rod.layer not in rods_by_layer:
                rods_by_layer[rod.layer] = []
            rods_by_layer[rod.layer].append(rod)

        # Check for crossings within each layer
        for layer_rods in rods_by_layer.values():
            for i, rod1 in enumerate(layer_rods):
                for rod2 in layer_rods[i + 1 :]:
                    if rod1.geometry.crosses(rod2.geometry):
                        return True

        return False

    def _push_to_undo_stack(self, operation: InfillEditOperation) -> None:
        """Push an operation to the undo stack."""
        # Clear redo stack when new operation is performed
        if self._redo_stack:
            self._redo_stack.clear()
            self.redo_available_changed.emit(False)

        # Add to undo stack
        self._undo_stack.append(operation)

        # Trim if exceeds max size
        while len(self._undo_stack) > self._max_history_size:
            self._undo_stack.pop(0)

        # Emit signal if this is the first item
        if len(self._undo_stack) == 1:
            self.undo_available_changed.emit(True)

    # Undo/redo operations

    def undo(self) -> bool:
        """
        Undo the most recent edit.

        Returns:
            True if undo was successful, False if nothing to undo
        """
        if not self._undo_stack:
            return False

        operation = self._undo_stack.pop()

        # Push to redo stack
        self._redo_stack.append(operation)
        if len(self._redo_stack) == 1:
            self.redo_available_changed.emit(True)

        # Emit undo available signal if stack is now empty
        if not self._undo_stack:
            self.undo_available_changed.emit(False)

        # Restore previous state
        self._project_model.set_railing_infill(operation.previous_infill)

        # Re-evaluate acceptability of restored infill
        _, is_acceptable = self._evaluate_infill(
            list(operation.previous_infill.rods),
            list(operation.previous_infill.anchor_points or []),
        )

        # Emit fitness scores signal
        self.fitness_scores_updated.emit(
            FitnessUpdate(
                old_score=operation.new_fitness_score,
                new_score=operation.previous_fitness_score,
                is_acceptable=is_acceptable,
            )
        )

        return True

    def redo(self) -> bool:
        """
        Redo the most recently undone edit.

        Returns:
            True if redo was successful, False if nothing to redo
        """
        if not self._redo_stack:
            return False

        operation = self._redo_stack.pop()

        # Push back to undo stack
        self._undo_stack.append(operation)
        if len(self._undo_stack) == 1:
            self.undo_available_changed.emit(True)

        # Emit redo available signal if stack is now empty
        if not self._redo_stack:
            self.redo_available_changed.emit(False)

        # Apply the operation
        self._project_model.set_railing_infill(operation.new_infill)

        # Re-evaluate acceptability of restored infill
        _, is_acceptable = self._evaluate_infill(
            list(operation.new_infill.rods),
            list(operation.new_infill.anchor_points or []),
        )

        # Emit fitness scores signal
        self.fitness_scores_updated.emit(
            FitnessUpdate(
                old_score=operation.previous_fitness_score,
                new_score=operation.new_fitness_score,
                is_acceptable=is_acceptable,
            )
        )

        return True

    def clear_history(self) -> None:
        """Clear both undo and redo histories."""
        had_undo = bool(self._undo_stack)
        had_redo = bool(self._redo_stack)

        self._undo_stack.clear()
        self._redo_stack.clear()

        if had_undo:
            self.undo_available_changed.emit(False)
        if had_redo:
            self.redo_available_changed.emit(False)
