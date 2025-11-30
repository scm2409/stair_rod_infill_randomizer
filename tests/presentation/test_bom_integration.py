"""Integration tests for BOM table with main window and viewport."""

import pytest
from pytestqt.qtbot import QtBot
from shapely.geometry import LineString, Polygon

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
