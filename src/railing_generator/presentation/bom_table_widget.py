"""BOM (Bill of Materials) table widget for displaying rod parts."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill


class BOMTableWidget(QWidget):
    """
    BOM (Bill of Materials) table widget with two tabs for frame and infill parts.

    Displays rod information in a table format with columns:
    - ID: Unique identifier
    - Length (cm): Rod length in centimeters
    - Start Angle (°): Cut angle at start point
    - End Angle (°): Cut angle at end point
    - Weight (kg): Rod weight in kilograms

    Features:
    - Two tabs: Frame Parts and Infill Parts
    - Sortable columns
    - Per-tab totals (sum length, sum weight)
    - Combined totals (total length, total weight)
    - Row selection triggers viewport highlighting

    Signals:
        frame_rod_selected: Emitted when a frame rod is selected (rod_id: int)
        infill_rod_selected: Emitted when an infill rod is selected (rod_id: int)
        selection_cleared: Emitted when selection is cleared
    """

    # Signals for rod selection
    frame_rod_selected = Signal(int)  # rod_id
    infill_rod_selected = Signal(int)  # rod_id
    selection_cleared = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the BOM table widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create frame parts tab
        self.frame_table = self._create_table()
        self.tab_widget.addTab(self.frame_table, "Frame Parts")

        # Create infill parts tab
        self.infill_table = self._create_table()
        self.tab_widget.addTab(self.infill_table, "Infill Parts")

        # Create totals labels
        self.frame_totals_label = QLabel("Frame Totals: Length: 0.00 cm, Weight: 0.000 kg")
        self.infill_totals_label = QLabel("Infill Totals: Length: 0.00 cm, Weight: 0.000 kg")
        self.combined_totals_label = QLabel("Combined Totals: Length: 0.00 cm, Weight: 0.000 kg")

        # Add totals labels to layout
        layout.addWidget(self.frame_totals_label)
        layout.addWidget(self.infill_totals_label)
        layout.addWidget(self.combined_totals_label)

        # Connect selection signals
        self.frame_table.itemSelectionChanged.connect(self._on_frame_selection_changed)
        self.infill_table.itemSelectionChanged.connect(self._on_infill_selection_changed)

        # Store current data for selection
        self._frame_rods: list[dict[str, float | int]] = []
        self._infill_rods: list[dict[str, float | int]] = []

    def _create_table(self) -> QTableWidget:
        """
        Create a table widget with BOM columns.

        Returns:
            Configured QTableWidget
        """
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["ID", "Length (cm)", "Start Angle (°)", "End Angle (°)", "Weight (kg)"]
        )

        # Enable sorting
        table.setSortingEnabled(True)

        # Configure column behavior
        header = table.horizontalHeader()
        assert header is not None
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Configure selection behavior
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        return table

    def set_frame_data(self, frame: RailingFrame | None) -> None:
        """
        Populate frame parts table from RailingFrame.

        Args:
            frame: RailingFrame containing frame rods, or None to clear
        """
        if frame is None:
            self._clear_frame_table()
            return

        # Convert rods to BOM entries
        self._frame_rods = [rod.to_bom_entry(i + 1) for i, rod in enumerate(frame.rods)]

        # Populate table
        self._populate_table(self.frame_table, self._frame_rods)

        # Update totals
        self._update_totals()

    def set_infill_data(self, infill: RailingInfill | None) -> None:
        """
        Populate infill parts table from RailingInfill.

        Args:
            infill: RailingInfill containing infill rods, or None to clear
        """
        if infill is None:
            self._clear_infill_table()
            return

        # Convert rods to BOM entries
        self._infill_rods = [rod.to_bom_entry(i + 1) for i, rod in enumerate(infill.rods)]

        # Populate table
        self._populate_table(self.infill_table, self._infill_rods)

        # Update totals
        self._update_totals()

    def _populate_table(
        self, table: QTableWidget, bom_entries: list[dict[str, float | int]]
    ) -> None:
        """
        Populate a table with BOM entries.

        Args:
            table: Table widget to populate
            bom_entries: List of BOM entry dictionaries
        """
        # Disable sorting during population for performance
        table.setSortingEnabled(False)

        # Set row count
        table.setRowCount(len(bom_entries))

        # Populate rows
        for row, entry in enumerate(bom_entries):
            # ID column (integer)
            id_item = QTableWidgetItem()
            id_item.setData(Qt.ItemDataRole.DisplayRole, entry["id"])
            table.setItem(row, 0, id_item)

            # Length column (float, 2 decimals)
            length_item = QTableWidgetItem()
            length_item.setData(Qt.ItemDataRole.DisplayRole, entry["length_cm"])
            table.setItem(row, 1, length_item)

            # Start angle column (float, 1 decimal)
            start_angle_item = QTableWidgetItem()
            start_angle_item.setData(Qt.ItemDataRole.DisplayRole, entry["start_cut_angle_deg"])
            table.setItem(row, 2, start_angle_item)

            # End angle column (float, 1 decimal)
            end_angle_item = QTableWidgetItem()
            end_angle_item.setData(Qt.ItemDataRole.DisplayRole, entry["end_cut_angle_deg"])
            table.setItem(row, 3, end_angle_item)

            # Weight column (float, 3 decimals)
            weight_item = QTableWidgetItem()
            weight_item.setData(Qt.ItemDataRole.DisplayRole, entry["weight_kg"])
            table.setItem(row, 4, weight_item)

        # Re-enable sorting
        table.setSortingEnabled(True)

    def _clear_frame_table(self) -> None:
        """Clear the frame parts table."""
        self._frame_rods = []
        self.frame_table.setRowCount(0)
        self._update_totals()

    def _clear_infill_table(self) -> None:
        """Clear the infill parts table."""
        self._infill_rods = []
        self.infill_table.setRowCount(0)
        self._update_totals()

    def _update_totals(self) -> None:
        """Update all totals labels."""
        # Calculate frame totals
        frame_total_length = sum(entry["length_cm"] for entry in self._frame_rods)
        frame_total_weight = sum(entry["weight_kg"] for entry in self._frame_rods)

        # Calculate infill totals
        infill_total_length = sum(entry["length_cm"] for entry in self._infill_rods)
        infill_total_weight = sum(entry["weight_kg"] for entry in self._infill_rods)

        # Calculate combined totals
        combined_total_length = frame_total_length + infill_total_length
        combined_total_weight = frame_total_weight + infill_total_weight

        # Update labels
        self.frame_totals_label.setText(
            f"Frame Totals: Length: {frame_total_length:.2f} cm, "
            f"Weight: {frame_total_weight:.3f} kg"
        )
        self.infill_totals_label.setText(
            f"Infill Totals: Length: {infill_total_length:.2f} cm, "
            f"Weight: {infill_total_weight:.3f} kg"
        )
        self.combined_totals_label.setText(
            f"Combined Totals: Length: {combined_total_length:.2f} cm, "
            f"Weight: {combined_total_weight:.3f} kg"
        )

    def _on_frame_selection_changed(self) -> None:
        """Handle frame table selection change."""
        selected_items = self.frame_table.selectedItems()
        if not selected_items:
            self.selection_cleared.emit()
            return

        # Get rod ID from first column of selected row
        row = selected_items[0].row()
        id_item = self.frame_table.item(row, 0)
        if id_item is not None:
            rod_id = id_item.data(Qt.ItemDataRole.DisplayRole)
            assert isinstance(rod_id, int)
            self.frame_rod_selected.emit(rod_id)

    def _on_infill_selection_changed(self) -> None:
        """Handle infill table selection change."""
        selected_items = self.infill_table.selectedItems()
        if not selected_items:
            self.selection_cleared.emit()
            return

        # Get rod ID from first column of selected row
        row = selected_items[0].row()
        id_item = self.infill_table.item(row, 0)
        if id_item is not None:
            rod_id = id_item.data(Qt.ItemDataRole.DisplayRole)
            assert isinstance(rod_id, int)
            self.infill_rod_selected.emit(rod_id)

    def clear_selection(self) -> None:
        """Clear selection in both tables."""
        self.frame_table.clearSelection()
        self.infill_table.clearSelection()
