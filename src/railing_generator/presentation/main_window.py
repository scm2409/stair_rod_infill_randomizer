"""Main application window."""

import logging
from pathlib import Path

from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.generation_progress import GenerationProgress
from railing_generator.presentation.bom_table_widget import BOMTableWidget
from railing_generator.presentation.parameter_panel import ParameterPanel
from railing_generator.presentation.progress_dialog import ProgressDialog
from railing_generator.presentation.viewport_widget import ViewportWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window for the Railing Infill Generator.

    Layout:
    - Menu bar with File, View, Help menus
    - Central viewport for rendering
    - Status bar for operation status
    """

    def __init__(
        self,
        project_model: RailingProjectModel,
        controller: ApplicationController,
    ) -> None:
        """
        Initialize the main window.

        Args:
            project_model: The central state model to observe
            controller: The application controller for user actions
        """
        super().__init__()

        # Store references to model and controller
        self.project_model = project_model
        self.controller = controller

        # Progress dialog (created on demand)
        self._progress_dialog: ProgressDialog | None = None

        # Window properties
        self.setWindowTitle("Untitled* - Railing Infill Generator")
        self.resize(1200, 800)

        # Create central widget with layout
        central_widget = QWidget()
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create parameter panel (left side)
        self.parameter_panel = ParameterPanel(project_model, controller)
        self.parameter_panel.setMinimumWidth(450)  # Ensure panel is wide enough
        self.parameter_panel.setMaximumWidth(450)  # Fixed width to accommodate all parameters
        layout.addWidget(self.parameter_panel)

        # Create right side container with viewport and BOM table
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for viewport and BOM table
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Create viewport (top of splitter, pass model for observation)
        self.viewport = ViewportWidget(project_model)
        splitter.addWidget(self.viewport)

        # Create BOM table (bottom of splitter)
        self.bom_table = BOMTableWidget()
        splitter.addWidget(self.bom_table)

        # Set initial splitter sizes (viewport gets 60%, BOM gets 40%)
        splitter.setSizes([600, 400])

        right_layout.addWidget(splitter)
        layout.addWidget(right_container, stretch=1)

        self.setCentralWidget(central_widget)

        # Create menu bar
        self._create_menu_bar()

        # Create status bar
        self._create_status_bar()

        # Connect to model signals for window title updates
        self._connect_model_signals()

        # Connect to controller signals for generation events
        self._connect_controller_signals()

        # Connect BOM table to model signals
        self._connect_bom_table_signals()

    def _create_menu_bar(self) -> None:
        """Create the menu bar with File, View, and Help menus."""
        menu_bar = self.menuBar()
        if menu_bar is None:
            menu_bar = QMenuBar(self)
            self.setMenuBar(menu_bar)

        # File menu
        file_menu = menu_bar.addMenu("&File")
        if file_menu is not None:
            # New Project action
            self.new_action = QAction("&New Project", self)
            self.new_action.setShortcut(QKeySequence.StandardKey.New)
            self.new_action.triggered.connect(self._on_new_project)
            file_menu.addAction(self.new_action)

            # Open action
            self.open_action = QAction("&Open...", self)
            self.open_action.setShortcut(QKeySequence.StandardKey.Open)
            self.open_action.triggered.connect(self._on_open_project)
            file_menu.addAction(self.open_action)

            file_menu.addSeparator()

            # Save action
            self.save_action = QAction("&Save", self)
            self.save_action.setShortcut(QKeySequence.StandardKey.Save)
            self.save_action.triggered.connect(self._on_save_project)
            file_menu.addAction(self.save_action)

            # Save As action
            self.save_as_action = QAction("Save &As...", self)
            self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
            self.save_as_action.triggered.connect(self._on_save_project_as)
            file_menu.addAction(self.save_as_action)

            file_menu.addSeparator()

            # Export to DXF action
            self.export_dxf_action = QAction("&Export to DXF...", self)
            self.export_dxf_action.triggered.connect(self._on_export_dxf)
            self.export_dxf_action.setEnabled(False)  # Disabled until a frame exists
            file_menu.addAction(self.export_dxf_action)

            file_menu.addSeparator()

            # Quit action
            self.quit_action = QAction("&Quit", self)
            self.quit_action.setShortcut(QKeySequence.StandardKey.Quit)
            self.quit_action.triggered.connect(self.close)
            file_menu.addAction(self.quit_action)

        # View menu
        view_menu = menu_bar.addMenu("&View")
        if view_menu is not None:
            # Create "Color Infill Layers by Layer" checkable action
            self.color_infill_layers_action = view_menu.addAction("Color Infill Layers by Layer")
            if self.color_infill_layers_action is not None:
                self.color_infill_layers_action.setCheckable(True)
                # Set initial state from model
                self.color_infill_layers_action.setChecked(
                    self.project_model.infill_layers_colored_by_layer
                )
                # Connect action to model's toggle method
                self.color_infill_layers_action.triggered.connect(
                    self.project_model.toggle_infill_layers_colored_by_layer
                )

        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        if help_menu is not None:
            # Placeholder actions - will be implemented in later tasks
            pass

    def _create_status_bar(self) -> None:
        """Create the status bar."""
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage("Ready")

    def _connect_model_signals(self) -> None:
        """Connect to model signals for observing state changes."""
        # Connect to project file path and modified state changes
        self.project_model.project_file_path_changed.connect(self._on_project_state_changed)
        self.project_model.project_modified_changed.connect(self._on_project_state_changed)

        # Connect to color mode changes to sync menu checkbox
        self.project_model.infill_layers_colored_by_layer_changed.connect(
            self._on_color_mode_changed
        )

        # Connect to frame updates to enable/disable Export DXF action
        self.project_model.railing_frame_updated.connect(self._on_frame_updated_for_export)

    def _connect_controller_signals(self) -> None:
        """Connect to controller signals for generation events."""
        # Connect to generation started signal to show progress dialog
        self.controller.generation_started.connect(self._on_generation_started)

    def _connect_bom_table_signals(self) -> None:
        """Connect BOM table to model signals and selection signals."""
        # Connect model signals to BOM table data updates
        self.project_model.railing_frame_updated.connect(self._on_frame_updated_for_bom)
        self.project_model.railing_infill_updated.connect(self._on_infill_updated_for_bom)

        # Connect BOM table selection signals to viewport highlighting
        self.bom_table.frame_rod_selected.connect(self._on_frame_rod_selected)
        self.bom_table.infill_rod_selected.connect(self._on_infill_rod_selected)
        self.bom_table.selection_cleared.connect(self._on_bom_selection_cleared)

    def _on_frame_updated_for_bom(self, frame: object) -> None:
        """
        Handle frame updates for BOM table.

        Args:
            frame: RailingFrame or None
        """
        from railing_generator.domain.railing_frame import RailingFrame

        if frame is None:
            self.bom_table.set_frame_data(None)
        else:
            assert isinstance(frame, RailingFrame)
            self.bom_table.set_frame_data(frame)

    def _on_infill_updated_for_bom(self, infill: object) -> None:
        """
        Handle infill updates for BOM table.

        Args:
            infill: RailingInfill or None
        """
        from railing_generator.domain.railing_infill import RailingInfill

        if infill is None:
            self.bom_table.set_infill_data(None)
        else:
            assert isinstance(infill, RailingInfill)
            self.bom_table.set_infill_data(infill)

    def _on_frame_rod_selected(self, rod_id: int) -> None:
        """
        Handle frame rod selection from BOM table.

        Args:
            rod_id: ID of the selected frame rod (1-based index)
        """
        logger.debug(f"Frame rod {rod_id} selected in BOM table")
        self.viewport.highlight_frame_rod(rod_id - 1)  # Convert to 0-based index

    def _on_infill_rod_selected(self, rod_id: int) -> None:
        """
        Handle infill rod selection from BOM table.

        Args:
            rod_id: ID of the selected infill rod (1-based index)
        """
        logger.debug(f"Infill rod {rod_id} selected in BOM table")
        self.viewport.highlight_infill_rod(rod_id - 1)  # Convert to 0-based index

    def _on_bom_selection_cleared(self) -> None:
        """Handle BOM selection cleared."""
        logger.debug("BOM selection cleared")
        self.viewport.clear_highlight()

    def _on_project_state_changed(self) -> None:
        """Handle project state changes (file path or modified flag)."""
        self._update_window_title()

    def _update_window_title(self) -> None:
        """Update the window title based on current project state."""
        # Get filename from project model
        file_path = self.project_model.project_file_path
        if file_path is None:
            filename = "Untitled"
        else:
            filename = file_path.name

        # Get modified flag from project model
        modified = self.project_model.project_modified

        # Build title
        title = filename
        if modified:
            title += "*"
        title += " - Railing Infill Generator"

        self.setWindowTitle(title)

    def _on_color_mode_changed(self, colored: bool) -> None:
        """
        Handle color mode changes from the model.

        Syncs the menu checkbox with the model state.

        Args:
            colored: True for colored mode, False for monochrome mode
        """
        self.color_infill_layers_action.setChecked(colored)

    def update_status(self, message: str) -> None:
        """
        Update the status bar message.

        Args:
            message: Status message to display
        """
        logger.debug(f"update_status() called with message: {message}")
        status_bar = self.statusBar()
        logger.debug(f"Got status bar: {status_bar}")
        if status_bar is not None:
            logger.debug("Setting status bar message")
            status_bar.showMessage(message)
            logger.debug("Status bar message set successfully")

    def _on_progress_updated(self, progress: GenerationProgress) -> None:
        """
        Handle progress updates during generation by updating status bar.

        Args:
            progress: GenerationProgress object from generator
        """

        # Store in model for use in completion message
        self.project_model.set_generation_progress(progress)

        # Get fitness from current RailingInfill (single source of truth)
        fitness = None
        if self.project_model.railing_infill is not None:
            fitness = self.project_model.railing_infill.fitness_score

        # Use the object's formatting method with fitness from RailingInfill
        status_message = progress.to_status_message(fitness=fitness)
        self.update_status(status_message)

    def _on_generation_completed(self, infill: object) -> None:
        """
        Handle generation completion by updating status.

        Args:
            infill: The generated infill result (ignored, just for signal compatibility)
        """
        logger.debug("MainWindow._on_generation_completed() called")
        logger.debug("About to call update_status")

        # Get final progress from model
        progress = self.project_model.generation_progress

        # Get fitness from RailingInfill (single source of truth)
        fitness = None
        if self.project_model.railing_infill is not None:
            fitness = self.project_model.railing_infill.fitness_score

        # Format with "Completed" prefix and fitness from RailingInfill
        status_message = progress.to_status_message(prefix="Completed", fitness=fitness)
        self.update_status(status_message)

        logger.debug("MainWindow._on_generation_completed() finished successfully")

    def _on_generation_failed(self, error_message: str) -> None:
        """
        Handle generation failure by updating status.

        Args:
            error_message: The error message from generation
        """
        logger.debug(f"MainWindow._on_generation_failed() called: {error_message}")

        # Get final progress from model
        progress = self.project_model.generation_progress

        # Get fitness from RailingInfill if available (single source of truth)
        fitness = None
        if self.project_model.railing_infill is not None:
            fitness = self.project_model.railing_infill.fitness_score

        # Format with "Failed" prefix and fitness from RailingInfill
        status_message = progress.to_status_message(prefix="Failed", fitness=fitness)
        self.update_status(status_message)

        logger.debug("MainWindow._on_generation_failed() finished successfully")

    def _on_best_result_updated(self, infill: object) -> None:
        """
        Handle best result updates during generation for real-time viewport updates.

        Args:
            infill: The best infill result found so far (RailingInfill)
        """
        logger.debug("MainWindow._on_best_result_updated() called - updating viewport")
        # Type narrowing: we trust this is RailingInfill from the signal
        from typing import cast

        from railing_generator.domain.railing_infill import RailingInfill

        logger.debug("About to cast infill")
        typed_infill = cast(RailingInfill, infill)
        logger.debug(f"Casted infill, has {len(typed_infill.rods)} rods")
        logger.debug("About to call project_model.set_railing_infill")
        self.project_model.set_railing_infill(typed_infill)
        logger.debug("project_model.set_railing_infill completed")
        logger.debug("MainWindow._on_best_result_updated() finished")

    def _on_generation_started(self, generator: object) -> None:
        """
        Handle generation started event by showing progress dialog.

        This method connects generator signals to UI components and shows
        the progress dialog non-blocking. All connections are made in the main thread,
        and Qt automatically handles cross-thread signal delivery using queued
        connections.

        Args:
            generator: The generator instance that was started (Generator)
        """
        logger.debug("MainWindow._on_generation_started() called")

        # Verify generator has required signals (duck typing approach)
        required_signals = [
            "progress_updated",
            "generation_completed",
            "generation_failed",
            "best_result_updated",
        ]
        for signal_name in required_signals:
            if not hasattr(generator, signal_name):
                raise TypeError(f"Generator missing required signal: {signal_name}")

        # Create progress dialog
        logger.debug("Creating ProgressDialog")
        self._progress_dialog = ProgressDialog(self, title="Generating Infill")

        # Connect generator signals to progress dialog
        # Qt will automatically use queued connections for cross-thread signals
        logger.debug("Connecting generator signals to progress dialog")
        generator.generation_completed.connect(self._progress_dialog.on_operation_completed)  # type: ignore[attr-defined]
        generator.generation_failed.connect(self._progress_dialog.on_operation_failed)  # type: ignore[attr-defined]

        # Connect generator signals to main window for status updates
        # Qt will automatically use queued connections for cross-thread signals
        logger.debug("Connecting generator signals to main window")
        generator.progress_updated.connect(self._on_progress_updated)  # type: ignore[attr-defined]
        generator.generation_completed.connect(self._on_generation_completed)  # type: ignore[attr-defined]
        generator.generation_failed.connect(self._on_generation_failed)  # type: ignore[attr-defined]

        # Connect generator signals for real-time viewport updates
        # Qt will automatically use queued connections for cross-thread signals
        generator.best_result_updated.connect(self._on_best_result_updated)  # type: ignore[attr-defined]

        # Connect progress dialog cancel button to controller
        self._progress_dialog.cancel_requested.connect(self.controller.cancel_generation)

        # Connect dialog's finished signal to cleanup method
        # Pass generator reference via lambda to cleanup method
        self._progress_dialog.finished.connect(lambda: self._cleanup_progress_dialog(generator))

        # Update status bar
        self.update_status("Generating infill...")

        # Show the dialog (non-blocking - allows event loop to continue)
        logger.debug("Showing progress dialog with show()")
        self._progress_dialog.show()
        logger.debug("MainWindow._on_generation_started() completed")

    def _cleanup_progress_dialog(self, generator: object) -> None:
        """
        Clean up progress dialog and disconnect all signals.

        This method is called when the dialog is closed (via finished signal).
        It safely disconnects all signals, handling cases where signals may
        already be disconnected or objects may be deleted.

        Args:
            generator: The generator instance whose signals need to be disconnected
        """
        logger.debug("MainWindow._cleanup_progress_dialog() called")

        if self._progress_dialog is None:
            logger.debug("Progress dialog already cleaned up")
            return

        # Disconnect all generator signals from dialog
        # Wrap each in try-except to handle RuntimeError and TypeError
        try:
            generator.generation_completed.disconnect(self._progress_dialog.on_operation_completed)  # type: ignore[attr-defined]
        except (RuntimeError, TypeError):
            logger.debug("generation_completed already disconnected or object deleted")

        try:
            generator.generation_failed.disconnect(self._progress_dialog.on_operation_failed)  # type: ignore[attr-defined]
        except (RuntimeError, TypeError):
            logger.debug("generation_failed already disconnected or object deleted")

        # Disconnect generator signals from main window
        logger.debug("Disconnecting generator signals from main window")
        try:
            generator.progress_updated.disconnect(self._on_progress_updated)  # type: ignore[attr-defined]
        except (RuntimeError, TypeError):
            logger.debug("progress_updated already disconnected or object deleted")

        try:
            generator.generation_completed.disconnect(self._on_generation_completed)  # type: ignore[attr-defined]
        except (RuntimeError, TypeError):
            logger.debug("generation_completed already disconnected or object deleted")

        try:
            generator.generation_failed.disconnect(self._on_generation_failed)  # type: ignore[attr-defined]
        except (RuntimeError, TypeError):
            logger.debug("generation_failed already disconnected or object deleted")

        try:
            generator.best_result_updated.disconnect(self._on_best_result_updated)  # type: ignore[attr-defined]
        except (RuntimeError, TypeError):
            logger.debug("best_result_updated already disconnected or object deleted")

        # Disconnect dialog's cancel_requested from controller
        logger.debug("Disconnecting dialog cancel_requested from controller")
        try:
            self._progress_dialog.cancel_requested.disconnect(self.controller.cancel_generation)
        except (RuntimeError, TypeError):
            logger.debug("cancel_requested already disconnected or object deleted")

        # Clear dialog reference
        self._progress_dialog = None
        logger.debug("MainWindow._cleanup_progress_dialog() completed")

    # =========================================================================
    # File Menu Actions
    # =========================================================================

    def _on_new_project(self) -> None:
        """Handle New Project action."""
        if not self._check_unsaved_changes():
            return

        self.controller.create_new_project()
        self.update_status("New project created")

    def _on_open_project(self) -> None:
        """Handle Open action."""
        if not self._check_unsaved_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "Railing Project Files (*.rig.zip);;All Files (*)",
        )

        if not file_path:
            return  # User cancelled

        logger.info(f"Opening project from: {file_path}")
        try:
            self.controller.load_project(Path(file_path))
            logger.info(f"Project loaded successfully from: {file_path}")
            self.update_status(f"Opened: {Path(file_path).name}")
        except Exception as e:
            logger.exception(f"Failed to open project from {file_path}: {e}")
            QMessageBox.critical(
                self,
                "Error Opening Project",
                f"Failed to open project:\n{e}",
            )

    def _on_save_project(self) -> None:
        """Handle Save action."""
        # If no file path, use Save As
        if self.project_model.project_file_path is None:
            self._on_save_project_as()
            return

        self._save_to_path(self.project_model.project_file_path)

    def _on_save_project_as(self) -> None:
        """Handle Save As action."""
        # Check if there's anything to save
        if not self.project_model.has_railing_frame():
            QMessageBox.warning(
                self,
                "Nothing to Save",
                "Please create a shape before saving.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            "",
            "Railing Project Files (*.rig.zip);;All Files (*)",
        )

        if not file_path:
            return  # User cancelled

        # Ensure .rig.zip extension
        if not file_path.endswith(".rig.zip"):
            file_path += ".rig.zip"

        self._save_to_path(Path(file_path))

    def _save_to_path(self, file_path: Path) -> None:
        """
        Save the project to the specified path.

        Args:
            file_path: Path to save the project to
        """
        logger.info(f"Saving project to: {file_path}")
        try:
            # Capture viewport as PNG
            logger.debug("Capturing viewport as PNG...")
            png_data = self.viewport.capture_as_png()
            logger.debug(f"PNG captured, size: {len(png_data)} bytes")

            logger.debug("Calling controller.save_project...")
            self.controller.save_project(file_path, png_data=png_data)
            logger.info(f"Project saved successfully to: {file_path}")
            self.update_status(f"Saved: {file_path.name}")
        except Exception as e:
            logger.exception(f"Failed to save project to {file_path}: {e}")
            QMessageBox.critical(
                self,
                "Error Saving Project",
                f"Failed to save project:\n{e}",
            )

    def _check_unsaved_changes(self) -> bool:
        """
        Check for unsaved changes and prompt user if necessary.

        Returns:
            True if it's safe to proceed (no changes or user chose to discard),
            False if user cancelled the operation
        """
        if not self.project_model.project_modified:
            return True

        result = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save before continuing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if result == QMessageBox.StandardButton.Save:
            self._on_save_project()
            # If still modified after save attempt, user cancelled save dialog
            return not self.project_model.project_modified
        elif result == QMessageBox.StandardButton.Discard:
            return True
        else:  # Cancel
            return False

    def _on_frame_updated_for_export(self, frame: object) -> None:
        """
        Handle frame updates to enable/disable Export DXF action.

        Args:
            frame: RailingFrame or None
        """
        # Enable Export DXF action only when a frame exists
        self.export_dxf_action.setEnabled(frame is not None)

    def _on_export_dxf(self) -> None:
        """Handle Export to DXF action."""
        # Check if there's anything to export
        if not self.project_model.has_railing_frame():
            QMessageBox.warning(
                self,
                "Nothing to Export",
                "Please create a shape before exporting to DXF.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to DXF",
            "",
            "DXF Files (*.dxf);;All Files (*)",
        )

        if not file_path:
            return  # User cancelled

        # Ensure .dxf extension
        if not file_path.lower().endswith(".dxf"):
            file_path += ".dxf"

        logger.info(f"Exporting DXF to: {file_path}")
        try:
            self.controller.export_dxf(Path(file_path))
            logger.info(f"DXF exported successfully to: {file_path}")
            self.update_status(f"Exported: {Path(file_path).name}")
        except Exception as e:
            logger.exception(f"Failed to export DXF to {file_path}: {e}")
            QMessageBox.critical(
                self,
                "Error Exporting DXF",
                f"Failed to export DXF:\n{e}",
            )

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle window close event.

        Prompts user about unsaved changes before closing.

        Args:
            event: The close event
        """
        # Skip unsaved changes check if _skip_close_confirmation is set (for testing)
        if getattr(self, "_skip_close_confirmation", False):
            event.accept()
            return

        if self._check_unsaved_changes():
            event.accept()
        else:
            event.ignore()
