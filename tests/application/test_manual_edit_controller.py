"""Tests for ManualEditController class."""

import pytest
from PySide6.QtCore import SignalInstance
from shapely.geometry import LineString

from railing_generator.application.manual_edit_controller import ManualEditController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.anchor_point import AnchorPoint
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod


class TestManualEditControllerInit:
    """Tests for ManualEditController initialization."""

    def test_init_with_project_model(self) -> None:
        """Test initialization with project model."""
        model = RailingProjectModel()
        controller = ManualEditController(model)

        assert controller.project_model is model
        assert controller.anchor_finder.search_radius_cm == 10.0
        assert controller.selected_anchor is None
        assert controller.selected_rod_index is None
        assert controller.has_selection is False

    def test_init_with_custom_search_radius(self) -> None:
        """Test initialization with custom search radius."""
        model = RailingProjectModel()
        controller = ManualEditController(model, search_radius_cm=15.0)

        assert controller.anchor_finder.search_radius_cm == 15.0

    def test_signals_exist(self) -> None:
        """Test that required signals are defined."""
        model = RailingProjectModel()
        controller = ManualEditController(model)

        assert isinstance(controller.selection_changed, SignalInstance)
        assert isinstance(controller.fitness_scores_updated, SignalInstance)


class TestSelectAnchorAt:
    """Tests for select_anchor_at method."""

    @pytest.fixture
    def model(self) -> RailingProjectModel:
        """Create a project model."""
        return RailingProjectModel()

    @pytest.fixture
    def controller(self, model: RailingProjectModel) -> ManualEditController:
        """Create a controller with 10.0 cm search radius."""
        return ManualEditController(model, search_radius_cm=10.0)

    @pytest.fixture
    def sample_anchors(self) -> list[AnchorPoint]:
        """Create sample anchor points."""
        return [
            AnchorPoint(
                position=(0.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
            AnchorPoint(
                position=(50.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=False,
            ),
            AnchorPoint(
                position=(100.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=True,  # Connected
            ),
        ]

    @pytest.fixture
    def sample_infill(self, sample_anchors: list[AnchorPoint]) -> RailingInfill:
        """Create sample infill with anchor points."""
        rod = Rod(
            geometry=LineString([(0, 0), (50, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )
        return RailingInfill(
            rods=[rod],
            anchor_points=sample_anchors,
        )

    def test_select_anchor_no_infill(
        self, controller: ManualEditController, model: RailingProjectModel
    ) -> None:
        """Test selection when no infill exists."""
        result = controller.select_anchor_at((0.0, 0.0))
        assert result is False
        assert controller.selected_anchor is None

    def test_select_anchor_no_anchor_points(
        self, controller: ManualEditController, model: RailingProjectModel
    ) -> None:
        """Test selection when infill has no anchor points."""
        infill = RailingInfill(rods=[], anchor_points=None)
        model.set_railing_infill(infill)

        result = controller.select_anchor_at((0.0, 0.0))
        assert result is False
        assert controller.selected_anchor is None

    def test_select_anchor_success(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
    ) -> None:
        """Test successful anchor selection (selects connected anchors)."""
        # Create infill with a connected anchor
        anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
            layer=1,
            used=True,  # Connected
        )
        rod = Rod(
            geometry=LineString([(0, 0), (50, 50)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )
        infill = RailingInfill(rods=[rod], anchor_points=[anchor])
        model.set_railing_infill(infill)

        result = controller.select_anchor_at((1.0, 0.0))  # Near (0, 0)
        assert result is True
        assert controller.selected_anchor is not None
        assert controller.selected_anchor.position == (0.0, 0.0)
        assert controller.has_selection is True

    def test_select_anchor_emits_signal(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
        qtbot: object,
    ) -> None:
        """Test that selection emits signal."""
        # Create infill with a connected anchor
        anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
            layer=1,
            used=True,
        )
        rod = Rod(
            geometry=LineString([(0, 0), (50, 50)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )
        infill = RailingInfill(rods=[rod], anchor_points=[anchor])
        model.set_railing_infill(infill)

        # Use qtbot to wait for signal
        with qtbot.waitSignal(controller.selection_changed, timeout=1000):  # type: ignore[union-attr]
            controller.select_anchor_at((1.0, 0.0))

    def test_select_anchor_skips_unconnected(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
        sample_infill: RailingInfill,
    ) -> None:
        """Test that unconnected anchors are skipped (we select connected ones)."""
        model.set_railing_infill(sample_infill)

        # Search near the unconnected anchor at (50, 0)
        result = controller.select_anchor_at((50.0, 0.0))
        # Should not find anything (unconnected anchors are skipped)
        assert result is False

    def test_select_anchor_outside_radius(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
    ) -> None:
        """Test selection when no anchor within radius."""
        # Create infill with a connected anchor far away
        anchor = AnchorPoint(
            position=(100.0, 100.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
            layer=1,
            used=True,
        )
        rod = Rod(
            geometry=LineString([(100, 100), (150, 150)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )
        infill = RailingInfill(rods=[rod], anchor_points=[anchor])
        model.set_railing_infill(infill)

        # Search far from any anchor
        result = controller.select_anchor_at((0.0, 0.0))
        assert result is False
        assert controller.selected_anchor is None

    def test_select_anchor_finds_rod_index(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
    ) -> None:
        """Test that rod index is found for connected anchor."""
        # Create infill where anchor matches rod endpoint
        anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
            layer=1,
            used=True,  # Must be connected (used) to be selectable
        )
        rod = Rod(
            geometry=LineString([(0, 0), (50, 50)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )
        infill = RailingInfill(rods=[rod], anchor_points=[anchor])
        model.set_railing_infill(infill)

        controller.select_anchor_at((0.0, 0.0))
        assert controller.selected_rod_index == 0


class TestClearSelection:
    """Tests for clear_selection method."""

    @pytest.fixture
    def model(self) -> RailingProjectModel:
        """Create a project model."""
        return RailingProjectModel()

    @pytest.fixture
    def controller(self, model: RailingProjectModel) -> ManualEditController:
        """Create a controller."""
        return ManualEditController(model)

    def test_clear_selection_when_none(self, controller: ManualEditController) -> None:
        """Test clearing selection when nothing is selected."""
        # Should not raise or emit signal
        controller.clear_selection()
        assert controller.selected_anchor is None
        assert controller.has_selection is False

    def test_clear_selection_with_selection(
        self, controller: ManualEditController, model: RailingProjectModel
    ) -> None:
        """Test clearing an existing selection."""
        # Set up selection with connected anchor
        anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
            layer=1,
            used=True,  # Must be connected to be selectable
        )
        rod = Rod(
            geometry=LineString([(0, 0), (50, 50)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )
        infill = RailingInfill(rods=[rod], anchor_points=[anchor])
        model.set_railing_infill(infill)
        controller.select_anchor_at((0.0, 0.0))

        assert controller.has_selection is True

        # Clear selection
        controller.clear_selection()
        assert controller.selected_anchor is None
        assert controller.selected_rod_index is None
        assert controller.has_selection is False

    def test_clear_selection_emits_signal(
        self, controller: ManualEditController, model: RailingProjectModel, qtbot: object
    ) -> None:
        """Test that clearing selection emits signal."""
        # Set up selection with connected anchor
        anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
            layer=1,
            used=True,  # Must be connected to be selectable
        )
        rod = Rod(
            geometry=LineString([(0, 0), (50, 50)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )
        infill = RailingInfill(rods=[rod], anchor_points=[anchor])
        model.set_railing_infill(infill)
        controller.select_anchor_at((0.0, 0.0))

        # Clear and check signal
        with qtbot.waitSignal(controller.selection_changed, timeout=1000):  # type: ignore[union-attr]
            controller.clear_selection()


class TestReconnectToAnchorAt:
    """Tests for reconnect_to_anchor_at method."""

    @pytest.fixture
    def model(self) -> RailingProjectModel:
        """Create a project model."""
        return RailingProjectModel()

    @pytest.fixture
    def controller(self, model: RailingProjectModel) -> ManualEditController:
        """Create a controller with 10.0 cm search radius."""
        return ManualEditController(model, search_radius_cm=10.0)

    @pytest.fixture
    def infill_with_rod(self) -> RailingInfill:
        """Create infill with a rod and anchor points."""
        # Create anchor points
        anchors = [
            AnchorPoint(
                position=(0.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=True,  # Start of rod
            ),
            AnchorPoint(
                position=(50.0, 50.0),
                frame_segment_index=1,
                is_vertical_segment=False,
                frame_segment_angle_deg=45.0,
                layer=1,
                used=True,  # End of rod
            ),
            AnchorPoint(
                position=(100.0, 0.0),
                frame_segment_index=2,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=None,
                used=False,  # Available target
            ),
        ]
        # Create rod connecting first two anchors
        rod = Rod(
            geometry=LineString([(0, 0), (50, 50)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )
        return RailingInfill(
            rods=[rod],
            anchor_points=anchors,
            fitness_score=0.72,
        )

    def test_reconnect_no_selection(
        self, controller: ManualEditController, model: RailingProjectModel
    ) -> None:
        """Test reconnection fails when no anchor is selected."""
        result = controller.reconnect_to_anchor_at((100.0, 0.0))
        assert result is False

    def test_reconnect_no_infill(
        self, controller: ManualEditController, model: RailingProjectModel
    ) -> None:
        """Test reconnection fails when no infill exists."""
        # Manually set selection state (bypassing normal flow)
        controller._selected_anchor = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
            layer=1,
            used=True,
        )
        controller._selected_rod_index = 0

        result = controller.reconnect_to_anchor_at((100.0, 0.0))
        assert result is False

    def test_reconnect_success(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
        infill_with_rod: RailingInfill,
    ) -> None:
        """Test successful rod reconnection."""
        model.set_railing_infill(infill_with_rod)

        # Select the start anchor (0, 0)
        controller.select_anchor_at((0.0, 0.0))
        assert controller.has_selection

        # Reconnect to target anchor (100, 0)
        result = controller.reconnect_to_anchor_at((100.0, 0.0))
        assert result is True

        # Verify new infill
        new_infill = model.railing_infill
        assert new_infill is not None
        assert len(new_infill.rods) == 1

        # Verify rod geometry changed
        new_rod = new_infill.rods[0]
        # The start point should now be at (100, 0)
        assert new_rod.start_point.x == pytest.approx(100.0)
        assert new_rod.start_point.y == pytest.approx(0.0)
        # End point should remain at (50, 50)
        assert new_rod.end_point.x == pytest.approx(50.0)
        assert new_rod.end_point.y == pytest.approx(50.0)

        # Selection should be cleared
        assert controller.has_selection is False

    def test_reconnect_updates_anchor_states(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
        infill_with_rod: RailingInfill,
    ) -> None:
        """Test that anchor states are updated after reconnection."""
        model.set_railing_infill(infill_with_rod)

        # Select the start anchor (0, 0)
        controller.select_anchor_at((0.0, 0.0))

        # Reconnect to target anchor (100, 0)
        controller.reconnect_to_anchor_at((100.0, 0.0))

        # Verify anchor states
        new_infill = model.railing_infill
        assert new_infill is not None
        assert new_infill.anchor_points is not None

        # Find anchors by position
        source_anchor = next(ap for ap in new_infill.anchor_points if ap.position == (0.0, 0.0))
        target_anchor = next(ap for ap in new_infill.anchor_points if ap.position == (100.0, 0.0))

        # Source should be marked as unused
        assert source_anchor.used is False
        # Target should be marked as used
        assert target_anchor.used is True

    def test_reconnect_adds_to_undo_stack(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
        infill_with_rod: RailingInfill,
    ) -> None:
        """Test that reconnection adds operation to undo stack."""
        model.set_railing_infill(infill_with_rod)

        assert controller.undo_stack_size == 0

        # Select and reconnect
        controller.select_anchor_at((0.0, 0.0))
        controller.reconnect_to_anchor_at((100.0, 0.0))

        assert controller.undo_stack_size == 1
        assert controller.can_undo is True

    def test_reconnect_no_target_found(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
        infill_with_rod: RailingInfill,
    ) -> None:
        """Test reconnection fails when no target anchor found."""
        model.set_railing_infill(infill_with_rod)

        # Select the start anchor
        controller.select_anchor_at((0.0, 0.0))

        # Try to reconnect to position far from any anchor
        result = controller.reconnect_to_anchor_at((500.0, 500.0))
        assert result is False

        # Undo stack should be empty
        assert controller.undo_stack_size == 0


class TestUndoRedo:
    """Tests for undo and redo functionality."""

    @pytest.fixture
    def model(self) -> RailingProjectModel:
        """Create a project model."""
        return RailingProjectModel()

    @pytest.fixture
    def controller(self, model: RailingProjectModel) -> ManualEditController:
        """Create a controller."""
        return ManualEditController(model)

    @pytest.fixture
    def infill_with_rod(self) -> RailingInfill:
        """Create infill with a rod and anchor points."""
        anchors = [
            AnchorPoint(
                position=(0.0, 0.0),
                frame_segment_index=0,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=1,
                used=True,
            ),
            AnchorPoint(
                position=(50.0, 50.0),
                frame_segment_index=1,
                is_vertical_segment=False,
                frame_segment_angle_deg=45.0,
                layer=1,
                used=True,
            ),
            AnchorPoint(
                position=(100.0, 0.0),
                frame_segment_index=2,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=None,
                used=False,
            ),
        ]
        rod = Rod(
            geometry=LineString([(0, 0), (50, 50)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )
        return RailingInfill(
            rods=[rod],
            anchor_points=anchors,
            fitness_score=0.72,
        )

    def test_undo_empty_stack(self, controller: ManualEditController) -> None:
        """Test undo with empty stack returns False."""
        result = controller.undo()
        assert result is False

    def test_redo_empty_stack(self, controller: ManualEditController) -> None:
        """Test redo with empty stack returns False."""
        result = controller.redo()
        assert result is False

    def test_undo_restores_previous_state(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
        infill_with_rod: RailingInfill,
    ) -> None:
        """Test that undo restores the previous infill state."""
        model.set_railing_infill(infill_with_rod)
        original_rod_start = infill_with_rod.rods[0].start_point

        # Perform edit
        controller.select_anchor_at((0.0, 0.0))
        controller.reconnect_to_anchor_at((100.0, 0.0))

        # Verify state changed
        assert model.railing_infill is not None
        assert model.railing_infill.rods[0].start_point.x != original_rod_start.x

        # Undo
        result = controller.undo()
        assert result is True

        # Verify state restored
        assert model.railing_infill is not None
        assert model.railing_infill.rods[0].start_point.x == pytest.approx(original_rod_start.x)
        assert model.railing_infill.rods[0].start_point.y == pytest.approx(original_rod_start.y)

    def test_redo_reapplies_edit(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
        infill_with_rod: RailingInfill,
    ) -> None:
        """Test that redo reapplies the undone edit."""
        model.set_railing_infill(infill_with_rod)

        # Perform edit
        controller.select_anchor_at((0.0, 0.0))
        controller.reconnect_to_anchor_at((100.0, 0.0))

        # Get the edited state
        edited_infill = model.railing_infill
        assert edited_infill is not None
        edited_start_x = edited_infill.rods[0].start_point.x

        # Undo
        controller.undo()

        # Redo
        result = controller.redo()
        assert result is True

        # Verify state matches edited state
        assert model.railing_infill is not None
        assert model.railing_infill.rods[0].start_point.x == pytest.approx(edited_start_x)

    def test_new_edit_clears_redo_stack(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
        infill_with_rod: RailingInfill,
    ) -> None:
        """Test that new edit clears the redo stack."""
        # Add another available anchor
        anchors = list(infill_with_rod.anchor_points) if infill_with_rod.anchor_points else []
        anchors.append(
            AnchorPoint(
                position=(150.0, 0.0),
                frame_segment_index=3,
                is_vertical_segment=True,
                frame_segment_angle_deg=0.0,
                layer=None,
                used=False,
            )
        )
        infill = RailingInfill(
            rods=infill_with_rod.rods,
            anchor_points=anchors,
            fitness_score=infill_with_rod.fitness_score,
        )
        model.set_railing_infill(infill)

        # Perform first edit
        controller.select_anchor_at((0.0, 0.0))
        controller.reconnect_to_anchor_at((100.0, 0.0))

        # Undo
        controller.undo()
        assert controller.can_redo is True

        # Perform new edit (should clear redo)
        controller.select_anchor_at((0.0, 0.0))
        controller.reconnect_to_anchor_at((150.0, 0.0))

        assert controller.can_redo is False

    def test_clear_history(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
        infill_with_rod: RailingInfill,
    ) -> None:
        """Test that clear_history clears both stacks."""
        model.set_railing_infill(infill_with_rod)

        # Perform edit
        controller.select_anchor_at((0.0, 0.0))
        controller.reconnect_to_anchor_at((100.0, 0.0))

        # Undo to populate redo stack
        controller.undo()

        assert controller.can_undo is False  # We undid the only operation
        assert controller.can_redo is True

        # Redo to have both stacks populated
        controller.redo()
        assert controller.can_undo is True

        # Clear history
        controller.clear_history()

        assert controller.can_undo is False
        assert controller.can_redo is False
        assert controller.undo_stack_size == 0
        assert controller.redo_stack_size == 0

    def test_max_history_size(self, model: RailingProjectModel) -> None:
        """Test that undo stack respects max history size."""
        controller = ManualEditController(model, max_history_size=3)

        # We'll manually push operations to test the max size limit
        # Create a simple infill for the operations
        anchor1 = AnchorPoint(
            position=(0.0, 0.0),
            frame_segment_index=0,
            is_vertical_segment=True,
            frame_segment_angle_deg=0.0,
            layer=1,
            used=True,
        )
        rod = Rod(
            geometry=LineString([(0, 0), (50, 50)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )
        infill = RailingInfill(rods=[rod], anchor_points=[anchor1])

        # Create dummy operations and push them directly
        from railing_generator.domain.infill_edit_operation import InfillEditOperation

        for i in range(5):
            operation = InfillEditOperation(
                previous_infill=infill,
                new_infill=infill,
                source_anchor_index=0,
                target_anchor_index=0,
                rod_index=0,
            )
            controller._push_to_undo_stack(operation)

        # Should only have 3 operations in stack (max_history_size)
        assert controller.undo_stack_size == 3

    def test_undo_emits_signals(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
        infill_with_rod: RailingInfill,
        qtbot: object,
    ) -> None:
        """Test that undo emits fitness_scores_updated signal."""
        model.set_railing_infill(infill_with_rod)

        # Perform edit
        controller.select_anchor_at((0.0, 0.0))
        controller.reconnect_to_anchor_at((100.0, 0.0))

        # Undo and check fitness signal is emitted
        with qtbot.waitSignal(controller.fitness_scores_updated, timeout=1000):  # type: ignore[union-attr]
            controller.undo()

    def test_redo_emits_signals(
        self,
        controller: ManualEditController,
        model: RailingProjectModel,
        infill_with_rod: RailingInfill,
        qtbot: object,
    ) -> None:
        """Test that redo emits fitness_scores_updated signal."""
        model.set_railing_infill(infill_with_rod)

        # Perform edit and undo
        controller.select_anchor_at((0.0, 0.0))
        controller.reconnect_to_anchor_at((100.0, 0.0))
        controller.undo()

        # Redo and check fitness signal is emitted
        with qtbot.waitSignal(controller.fitness_scores_updated, timeout=1000):  # type: ignore[union-attr]
            controller.redo()
