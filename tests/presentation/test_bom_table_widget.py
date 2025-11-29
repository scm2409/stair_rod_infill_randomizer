"""Tests for BOM table widget."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTabWidget
from pytestqt.qtbot import QtBot
from shapely.geometry import LineString, Polygon

from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod
from railing_generator.presentation.bom_table_widget import BOMTableWidget


@pytest.fixture
def bom_widget(qtbot: QtBot) -> BOMTableWidget:
    """Create a BOM table widget for testing."""
    widget = BOMTableWidget()
    qtbot.addWidget(widget)
    return widget


def test_bom_widget_initialization(bom_widget: BOMTableWidget) -> None:
    """Test that BOM widget initializes with correct structure."""
    # Check tab widget exists
    assert isinstance(bom_widget.tab_widget, QTabWidget)
    assert bom_widget.tab_widget.count() == 2

    # Check tab names
    assert bom_widget.tab_widget.tabText(0) == "Frame Parts"
    assert bom_widget.tab_widget.tabText(1) == "Infill Parts"

    # Check tables exist
    assert isinstance(bom_widget.frame_table, QTableWidget)
    assert isinstance(bom_widget.infill_table, QTableWidget)


def test_table_columns(bom_widget: BOMTableWidget) -> None:
    """Test that tables have correct columns."""
    expected_headers = ["ID", "Length (cm)", "Start Angle (°)", "End Angle (°)", "Weight (kg)"]

    # Check frame table columns
    assert bom_widget.frame_table.columnCount() == 5
    for col, expected_header in enumerate(expected_headers):
        actual_header = bom_widget.frame_table.horizontalHeaderItem(col)
        assert actual_header is not None
        assert actual_header.text() == expected_header

    # Check infill table columns
    assert bom_widget.infill_table.columnCount() == 5
    for col, expected_header in enumerate(expected_headers):
        actual_header = bom_widget.infill_table.horizontalHeaderItem(col)
        assert actual_header is not None
        assert actual_header.text() == expected_header


def test_table_sorting_enabled(bom_widget: BOMTableWidget) -> None:
    """Test that tables have sorting enabled."""
    assert bom_widget.frame_table.isSortingEnabled()
    assert bom_widget.infill_table.isSortingEnabled()


def test_totals_labels_exist(bom_widget: BOMTableWidget) -> None:
    """Test that totals labels exist and have initial values."""
    # Check frame totals label
    assert "Frame Totals:" in bom_widget.frame_totals_label.text()
    assert "Length: 0.00 cm" in bom_widget.frame_totals_label.text()
    assert "Weight: 0.000 kg" in bom_widget.frame_totals_label.text()

    # Check infill totals label
    assert "Infill Totals:" in bom_widget.infill_totals_label.text()
    assert "Length: 0.00 cm" in bom_widget.infill_totals_label.text()
    assert "Weight: 0.000 kg" in bom_widget.infill_totals_label.text()

    # Check combined totals label
    assert "Combined Totals:" in bom_widget.combined_totals_label.text()
    assert "Length: 0.00 cm" in bom_widget.combined_totals_label.text()
    assert "Weight: 0.000 kg" in bom_widget.combined_totals_label.text()


def test_initial_state_empty(bom_widget: BOMTableWidget) -> None:
    """Test that tables start empty."""
    assert bom_widget.frame_table.rowCount() == 0
    assert bom_widget.infill_table.rowCount() == 0


@pytest.fixture
def sample_frame() -> RailingFrame:
    """Create a sample railing frame for testing."""
    # Create 3 frame rods
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
        Rod(
            geometry=LineString([(0, 100), (100, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
    ]

    # Create boundary polygon
    boundary = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])

    return RailingFrame(rods=rods, boundary=boundary)


@pytest.fixture
def sample_infill() -> RailingInfill:
    """Create a sample railing infill for testing."""
    # Create 2 infill rods
    rods = [
        Rod(
            geometry=LineString([(25, 0), (25, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        ),
        Rod(
            geometry=LineString([(75, 0), (75, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        ),
    ]

    return RailingInfill(rods=rods, fitness_score=0.8, iteration_count=10, duration_sec=1.5)


def test_set_frame_data_populates_table(
    bom_widget: BOMTableWidget, sample_frame: RailingFrame
) -> None:
    """Test that setting frame data populates the frame table."""
    bom_widget.set_frame_data(sample_frame)

    # Check row count
    assert bom_widget.frame_table.rowCount() == 3

    # Check first row data
    assert bom_widget.frame_table.item(0, 0).data(Qt.ItemDataRole.DisplayRole) == 1  # ID
    assert bom_widget.frame_table.item(0, 1).data(Qt.ItemDataRole.DisplayRole) == 100.0  # Length
    assert bom_widget.frame_table.item(0, 2).data(Qt.ItemDataRole.DisplayRole) == 0.0  # Start angle
    assert bom_widget.frame_table.item(0, 3).data(Qt.ItemDataRole.DisplayRole) == 0.0  # End angle
    assert bom_widget.frame_table.item(0, 4).data(Qt.ItemDataRole.DisplayRole) == 0.5  # Weight


def test_set_infill_data_populates_table(
    bom_widget: BOMTableWidget, sample_infill: RailingInfill
) -> None:
    """Test that setting infill data populates the infill table."""
    bom_widget.set_infill_data(sample_infill)

    # Check row count
    assert bom_widget.infill_table.rowCount() == 2

    # Check first row data
    assert bom_widget.infill_table.item(0, 0).data(Qt.ItemDataRole.DisplayRole) == 1  # ID
    assert bom_widget.infill_table.item(0, 1).data(Qt.ItemDataRole.DisplayRole) == 100.0  # Length
    assert (
        bom_widget.infill_table.item(0, 2).data(Qt.ItemDataRole.DisplayRole) == 0.0
    )  # Start angle
    assert bom_widget.infill_table.item(0, 3).data(Qt.ItemDataRole.DisplayRole) == 0.0  # End angle
    assert bom_widget.infill_table.item(0, 4).data(Qt.ItemDataRole.DisplayRole) == 0.3  # Weight


def test_frame_totals_calculation(bom_widget: BOMTableWidget, sample_frame: RailingFrame) -> None:
    """Test that frame totals are calculated correctly."""
    bom_widget.set_frame_data(sample_frame)

    # Expected: 3 rods * 100 cm = 300 cm total length
    # Expected: 3 rods * 100 cm * 0.5 kg/m / 100 = 1.5 kg total weight
    assert "Length: 300.00 cm" in bom_widget.frame_totals_label.text()
    assert "Weight: 1.500 kg" in bom_widget.frame_totals_label.text()


def test_infill_totals_calculation(
    bom_widget: BOMTableWidget, sample_infill: RailingInfill
) -> None:
    """Test that infill totals are calculated correctly."""
    bom_widget.set_infill_data(sample_infill)

    # Expected: 2 rods * 100 cm = 200 cm total length
    # Expected: 2 rods * 100 cm * 0.3 kg/m / 100 = 0.6 kg total weight
    assert "Length: 200.00 cm" in bom_widget.infill_totals_label.text()
    assert "Weight: 0.600 kg" in bom_widget.infill_totals_label.text()


def test_combined_totals_calculation(
    bom_widget: BOMTableWidget, sample_frame: RailingFrame, sample_infill: RailingInfill
) -> None:
    """Test that combined totals are calculated correctly."""
    bom_widget.set_frame_data(sample_frame)
    bom_widget.set_infill_data(sample_infill)

    # Expected: 300 cm (frame) + 200 cm (infill) = 500 cm
    # Expected: 1.5 kg (frame) + 0.6 kg (infill) = 2.1 kg
    assert "Length: 500.00 cm" in bom_widget.combined_totals_label.text()
    assert "Weight: 2.100 kg" in bom_widget.combined_totals_label.text()


def test_set_frame_data_none_clears_table(bom_widget: BOMTableWidget) -> None:
    """Test that setting frame data to None clears the table."""
    # First populate with data
    rods = [
        Rod(
            geometry=LineString([(0, 0), (0, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        )
    ]
    boundary = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    frame = RailingFrame(rods=rods, boundary=boundary)
    bom_widget.set_frame_data(frame)

    # Verify data is present
    assert bom_widget.frame_table.rowCount() == 1

    # Clear data
    bom_widget.set_frame_data(None)

    # Verify table is cleared
    assert bom_widget.frame_table.rowCount() == 0
    assert "Length: 0.00 cm" in bom_widget.frame_totals_label.text()


def test_set_infill_data_none_clears_table(bom_widget: BOMTableWidget) -> None:
    """Test that setting infill data to None clears the table."""
    # First populate with data
    rods = [
        Rod(
            geometry=LineString([(0, 0), (0, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        )
    ]
    infill = RailingInfill(rods=rods)
    bom_widget.set_infill_data(infill)

    # Verify data is present
    assert bom_widget.infill_table.rowCount() == 1

    # Clear data
    bom_widget.set_infill_data(None)

    # Verify table is cleared
    assert bom_widget.infill_table.rowCount() == 0
    assert "Length: 0.00 cm" in bom_widget.infill_totals_label.text()


def test_frame_rod_selection_emits_signal(
    qtbot: QtBot, bom_widget: BOMTableWidget, sample_frame: RailingFrame
) -> None:
    """Test that selecting a frame rod emits the correct signal."""
    bom_widget.set_frame_data(sample_frame)

    # Connect signal spy
    with qtbot.waitSignal(bom_widget.frame_rod_selected, timeout=1000) as blocker:
        # Select first row
        bom_widget.frame_table.selectRow(0)

    # Verify signal was emitted with correct rod ID
    assert blocker.args == [1]


def test_infill_rod_selection_emits_signal(
    qtbot: QtBot, bom_widget: BOMTableWidget, sample_infill: RailingInfill
) -> None:
    """Test that selecting an infill rod emits the correct signal."""
    bom_widget.set_infill_data(sample_infill)

    # Connect signal spy
    with qtbot.waitSignal(bom_widget.infill_rod_selected, timeout=1000) as blocker:
        # Select first row
        bom_widget.infill_table.selectRow(0)

    # Verify signal was emitted with correct rod ID
    assert blocker.args == [1]


def test_clear_selection_clears_both_tables(
    bom_widget: BOMTableWidget, sample_frame: RailingFrame, sample_infill: RailingInfill
) -> None:
    """Test that clear_selection clears both tables."""
    bom_widget.set_frame_data(sample_frame)
    bom_widget.set_infill_data(sample_infill)

    # Select rows in both tables
    bom_widget.frame_table.selectRow(0)
    bom_widget.infill_table.selectRow(0)

    # Verify selections exist
    assert len(bom_widget.frame_table.selectedItems()) > 0
    assert len(bom_widget.infill_table.selectedItems()) > 0

    # Clear selection
    bom_widget.clear_selection()

    # Verify selections are cleared
    assert len(bom_widget.frame_table.selectedItems()) == 0
    assert len(bom_widget.infill_table.selectedItems()) == 0


def test_selection_cleared_signal_on_deselect(
    qtbot: QtBot, bom_widget: BOMTableWidget, sample_frame: RailingFrame
) -> None:
    """Test that deselecting emits selection_cleared signal."""
    bom_widget.set_frame_data(sample_frame)

    # Select first row
    bom_widget.frame_table.selectRow(0)

    # Connect signal spy
    with qtbot.waitSignal(bom_widget.selection_cleared, timeout=1000):
        # Clear selection
        bom_widget.frame_table.clearSelection()
