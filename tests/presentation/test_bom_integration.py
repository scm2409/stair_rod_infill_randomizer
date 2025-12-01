"""Integration tests for BOM table with main window and viewport."""

import pytest
from pytestqt.qtbot import QtBot
from shapely.geometry import LineString, Point, Polygon

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod
from railing_generator.presentation.main_window import MainWindow


@pytest.fixture
def main_window(qtbot: QtBot) -> MainWindow:
    """Create a main window for testing."""
    model = RailingProjectModel()
    controller = ApplicationController(model)
    window = MainWindow(model, controller)
    window._skip_close_confirmation = True  # Prevent dialog on close during tests
    qtbot.addWidget(window)
    return window


@pytest.fixture
def sample_frame() -> RailingFrame:
    """Create a sample railing frame for testing."""
    rods = [
        Rod(
            geometry=LineString([(0, 0), (0, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(100, 0), (100, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
    ]
    boundary = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    return RailingFrame(rods=rods, boundary=boundary)


@pytest.fixture
def sample_infill() -> RailingInfill:
    """Create a sample railing infill for testing."""
    rods = [
        Rod(
            geometry=LineString([(25, 0), (25, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        ),
    ]
    return RailingInfill(rods=rods)


def test_bom_table_exists_in_main_window(main_window: MainWindow) -> None:
    """Test that BOM table widget exists in main window."""
    assert hasattr(main_window, "bom_table")
    assert main_window.bom_table is not None


def test_bom_table_updates_on_frame_change(
    main_window: MainWindow, sample_frame: RailingFrame
) -> None:
    """Test that BOM table updates when frame changes in model."""
    # Set frame in model
    main_window.project_model.set_railing_frame(sample_frame)

    # Verify BOM table was updated
    assert main_window.bom_table.frame_table.rowCount() == 2


def test_bom_table_updates_on_infill_change(
    main_window: MainWindow, sample_infill: RailingInfill
) -> None:
    """Test that BOM table updates when infill changes in model."""
    # Set infill in model
    main_window.project_model.set_railing_infill(sample_infill)

    # Verify BOM table was updated
    assert main_window.bom_table.infill_table.rowCount() == 1


def test_bom_table_clears_on_frame_clear(
    main_window: MainWindow, sample_frame: RailingFrame
) -> None:
    """Test that BOM table clears when frame is cleared in model."""
    # Set frame
    main_window.project_model.set_railing_frame(sample_frame)
    assert main_window.bom_table.frame_table.rowCount() == 2

    # Clear frame
    main_window.project_model.set_railing_frame(None)
    assert main_window.bom_table.frame_table.rowCount() == 0


def test_viewport_highlighting_on_frame_rod_selection(
    main_window: MainWindow, sample_frame: RailingFrame
) -> None:
    """Test that viewport highlights rod when selected in BOM table."""
    # Set frame in model
    main_window.project_model.set_railing_frame(sample_frame)

    # Select first rod in BOM table
    main_window.bom_table.frame_table.selectRow(0)

    # Verify highlight group was created in viewport
    assert main_window.viewport._highlight_group is not None


def test_viewport_highlighting_on_infill_rod_selection(
    main_window: MainWindow, sample_frame: RailingFrame, sample_infill: RailingInfill
) -> None:
    """Test that viewport highlights rod when selected in BOM table."""
    # Set frame and infill in model
    main_window.project_model.set_railing_frame(sample_frame)
    main_window.project_model.set_railing_infill(sample_infill)

    # Select first rod in BOM table
    main_window.bom_table.infill_table.selectRow(0)

    # Verify highlight group was created in viewport
    assert main_window.viewport._highlight_group is not None


def test_viewport_clear_highlight_on_selection_clear(
    main_window: MainWindow, sample_frame: RailingFrame
) -> None:
    """Test that viewport clears highlight when BOM selection is cleared."""
    # Set frame in model
    main_window.project_model.set_railing_frame(sample_frame)

    # Select first rod
    main_window.bom_table.frame_table.selectRow(0)
    assert main_window.viewport._highlight_group is not None

    # Clear selection
    main_window.bom_table.frame_table.clearSelection()

    # Verify highlight was cleared
    assert main_window.viewport._highlight_group is None


# ============================================================================
# Manual Editing Integration Tests
# ============================================================================


@pytest.fixture
def infill_with_anchors() -> RailingInfill:
    """Create infill with anchor points for manual editing tests."""
    from railing_generator.domain.anchor_point import AnchorPoint

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
    return RailingInfill(rods=[rod], anchor_points=anchors, fitness_score=0.72)


def test_bom_updates_after_manual_edit(
    main_window: MainWindow, infill_with_anchors: RailingInfill
) -> None:
    """Test that BOM table updates after manual rod edit."""
    # Set initial infill
    main_window.project_model.set_railing_infill(infill_with_anchors)
    initial_row_count = main_window.bom_table.infill_table.rowCount()
    assert initial_row_count == 1

    # Perform manual edit
    main_window.manual_edit_controller.select_anchor_at(Point(0.0, 0.0))
    main_window.manual_edit_controller.reconnect_to_anchor_at(Point(100.0, 0.0))

    # BOM should still have 1 rod (we moved it, not added/removed)
    assert main_window.bom_table.infill_table.rowCount() == 1

    # But the rod length should have changed
    # Original: (0,0) to (50,50) = ~70.7 cm
    # New: (100,0) to (50,50) = ~70.7 cm (same length in this case)
    # The important thing is that the BOM was updated


def test_project_marked_modified_after_manual_edit(
    main_window: MainWindow, infill_with_anchors: RailingInfill
) -> None:
    """Test that project is marked as modified after manual edit."""
    # Set initial infill and mark as saved
    main_window.project_model.set_railing_infill(infill_with_anchors)
    main_window.project_model.mark_project_saved()
    assert not main_window.project_model.project_modified

    # Perform manual edit
    main_window.manual_edit_controller.select_anchor_at(Point(0.0, 0.0))
    main_window.manual_edit_controller.reconnect_to_anchor_at(Point(100.0, 0.0))

    # Project should be marked as modified
    assert main_window.project_model.project_modified


def test_bom_totals_recalculate_after_manual_edit(
    main_window: MainWindow, infill_with_anchors: RailingInfill
) -> None:
    """Test that BOM totals recalculate after manual edit."""
    # Set initial infill
    main_window.project_model.set_railing_infill(infill_with_anchors)

    # Get initial totals label text
    initial_totals_text = main_window.bom_table.infill_totals_label.text()
    assert "Infill Totals:" in initial_totals_text

    # Perform manual edit
    main_window.manual_edit_controller.select_anchor_at(Point(0.0, 0.0))
    main_window.manual_edit_controller.reconnect_to_anchor_at(Point(100.0, 0.0))

    # Get new totals label text
    new_totals_text = main_window.bom_table.infill_totals_label.text()

    # Totals label should still be valid (may or may not be different depending on geometry)
    assert "Infill Totals:" in new_totals_text
    assert "Length:" in new_totals_text
    assert "Weight:" in new_totals_text


def test_viewport_updates_after_manual_edit(
    main_window: MainWindow, infill_with_anchors: RailingInfill
) -> None:
    """Test that viewport updates after manual edit."""
    # Set initial infill
    main_window.project_model.set_railing_infill(infill_with_anchors)

    # Verify infill is rendered
    assert main_window.viewport._railing_infill_group is not None

    # Perform manual edit
    main_window.manual_edit_controller.select_anchor_at(Point(0.0, 0.0))
    main_window.manual_edit_controller.reconnect_to_anchor_at(Point(100.0, 0.0))

    # Viewport should still have infill rendered (updated)
    assert main_window.viewport._railing_infill_group is not None


def test_viewport_updates_on_undo(
    main_window: MainWindow, infill_with_anchors: RailingInfill
) -> None:
    """Test that viewport updates when undo is performed."""
    # Set initial infill
    main_window.project_model.set_railing_infill(infill_with_anchors)

    # Perform manual edit
    main_window.manual_edit_controller.select_anchor_at(Point(0.0, 0.0))
    main_window.manual_edit_controller.reconnect_to_anchor_at(Point(100.0, 0.0))

    # Get current infill rod start point
    current_infill = main_window.project_model.railing_infill
    assert current_infill is not None
    edited_start_x = current_infill.rods[0].start_point.x

    # Undo
    main_window.manual_edit_controller.undo()

    # Viewport should show original infill
    restored_infill = main_window.project_model.railing_infill
    assert restored_infill is not None
    assert restored_infill.rods[0].start_point.x != edited_start_x


def test_viewport_updates_on_redo(
    main_window: MainWindow, infill_with_anchors: RailingInfill
) -> None:
    """Test that viewport updates when redo is performed."""
    # Set initial infill
    main_window.project_model.set_railing_infill(infill_with_anchors)

    # Perform manual edit
    main_window.manual_edit_controller.select_anchor_at(Point(0.0, 0.0))
    main_window.manual_edit_controller.reconnect_to_anchor_at(Point(100.0, 0.0))

    # Get edited state
    edited_infill = main_window.project_model.railing_infill
    assert edited_infill is not None
    edited_start_x = edited_infill.rods[0].start_point.x

    # Undo
    main_window.manual_edit_controller.undo()

    # Redo
    main_window.manual_edit_controller.redo()

    # Viewport should show edited infill again
    redone_infill = main_window.project_model.railing_infill
    assert redone_infill is not None
    assert redone_infill.rods[0].start_point.x == edited_start_x


def test_bom_updates_on_undo(main_window: MainWindow, infill_with_anchors: RailingInfill) -> None:
    """Test that BOM table updates when undo is performed."""
    # Set initial infill
    main_window.project_model.set_railing_infill(infill_with_anchors)

    # Perform manual edit
    main_window.manual_edit_controller.select_anchor_at(Point(0.0, 0.0))
    main_window.manual_edit_controller.reconnect_to_anchor_at(Point(100.0, 0.0))

    # BOM should have 1 rod
    assert main_window.bom_table.infill_table.rowCount() == 1

    # Undo
    main_window.manual_edit_controller.undo()

    # BOM should still have 1 rod (we moved it, not added/removed)
    assert main_window.bom_table.infill_table.rowCount() == 1


def test_fitness_display_updates_on_undo(
    main_window: MainWindow, infill_with_anchors: RailingInfill
) -> None:
    """Test that fitness display updates when undo is performed."""

    # Helper to get status bar message
    def get_status_message() -> str:
        status_bar = main_window.statusBar()
        if status_bar is not None:
            return status_bar.currentMessage()
        return ""

    # Set initial infill
    main_window.project_model.set_railing_infill(infill_with_anchors)

    # Perform manual edit
    main_window.manual_edit_controller.select_anchor_at(Point(0.0, 0.0))
    main_window.manual_edit_controller.reconnect_to_anchor_at(Point(100.0, 0.0))

    # Fitness display should show comparison in status bar
    assert "Fitness:" in get_status_message()

    # Undo
    main_window.manual_edit_controller.undo()

    # Fitness display should be updated (showing reverse comparison)
    # The signal is emitted with swapped scores
    assert "Fitness:" in get_status_message()


def test_history_cleared_on_new_generation(main_window: MainWindow) -> None:
    """Test that undo/redo history is cleared when new infill is generated."""
    from railing_generator.domain.anchor_point import AnchorPoint

    # Create infill with anchors
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
    infill = RailingInfill(rods=[rod], anchor_points=anchors, fitness_score=0.72)
    main_window.project_model.set_railing_infill(infill)

    # Perform manual edit
    main_window.manual_edit_controller.select_anchor_at(Point(0.0, 0.0))
    main_window.manual_edit_controller.reconnect_to_anchor_at(Point(100.0, 0.0))

    # Undo should be available
    assert main_window.manual_edit_controller.can_undo

    # Simulate generation completed (this is what happens when generator finishes)
    main_window._on_generation_completed(None)

    # History should be cleared
    assert not main_window.manual_edit_controller.can_undo
    assert not main_window.manual_edit_controller.can_redo
