"""Main application window."""

from PySide6.QtWidgets import QMainWindow, QMenuBar

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.presentation.viewport_widget import ViewportWidget


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

        # Window properties
        self.setWindowTitle("Untitled* - Railing Infill Generator")
        self.resize(1200, 800)

        # Create viewport as central widget (pass model for observation)
        self.viewport = ViewportWidget(project_model)
        self.setCentralWidget(self.viewport)

        # Create menu bar
        self._create_menu_bar()

        # Create status bar
        self._create_status_bar()

        # Connect to model signals for window title updates
        self._connect_model_signals()

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
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage(message)
