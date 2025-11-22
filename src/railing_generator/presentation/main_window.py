"""Main application window."""

import logging

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QMenuBar, QWidget

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
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
        self.parameter_panel.setMaximumWidth(350)
        layout.addWidget(self.parameter_panel)

        # Create viewport (right side, pass model for observation)
        self.viewport = ViewportWidget(project_model)
        layout.addWidget(self.viewport, stretch=1)

        self.setCentralWidget(central_widget)

        # Create menu bar
        self._create_menu_bar()

        # Create status bar
        self._create_status_bar()

        # Connect to model signals for window title updates
        self._connect_model_signals()

        # Connect to controller signals for generation events
        self._connect_controller_signals()

    def _create_menu_bar(self) -> None:
        """Create the menu bar with File, View, and Help menus."""
        menu_bar = self.menuBar()
        if menu_bar is None:
            menu_bar = QMenuBar(self)
            self.setMenuBar(menu_bar)

        # File menu
        file_menu = menu_bar.addMenu("&File")
        if file_menu is not None:
            # Placeholder actions - will be implemented in later tasks
            pass

        # View menu
        view_menu = menu_bar.addMenu("&View")
        if view_menu is not None:
            # Placeholder actions - will be implemented in later tasks
            pass

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

    def _connect_controller_signals(self) -> None:
        """Connect to controller signals for generation events."""
        # Connect to generation started signal to show progress dialog
        self.controller.generation_started.connect(self._on_generation_started)

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

    def _on_generation_completed(self, infill: object) -> None:
        """
        Handle generation completion by updating status.

        Args:
            infill: The generated infill result (ignored, just for signal compatibility)
        """
        logger.debug("MainWindow._on_generation_completed() called")
        logger.debug("About to call update_status")
        self.update_status("Generation completed successfully")
        logger.debug("MainWindow._on_generation_completed() finished successfully")

    def _on_generation_failed(self, error_message: str) -> None:
        """
        Handle generation failure by updating status.

        Args:
            error_message: The error message from generation
        """
        logger.debug(f"MainWindow._on_generation_failed() called: {error_message}")
        self.update_status(f"Generation failed: {error_message}")
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
        generator.progress_updated.connect(self._progress_dialog.update_progress)  # type: ignore[attr-defined]
        generator.generation_completed.connect(self._progress_dialog.on_operation_completed)  # type: ignore[attr-defined]
        generator.generation_failed.connect(self._progress_dialog.on_operation_failed)  # type: ignore[attr-defined]

        # Connect generator signals to main window for status updates
        # Qt will automatically use queued connections for cross-thread signals
        logger.debug("Connecting generator signals to main window")
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
        logger.debug("Disconnecting generator signals from dialog")
        try:
            generator.progress_updated.disconnect(self._progress_dialog.update_progress)  # type: ignore[attr-defined]
        except (RuntimeError, TypeError):
            logger.debug("progress_updated already disconnected or object deleted")

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
