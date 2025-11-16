"""Main application window."""

from PySide6.QtWidgets import QMainWindow, QMenuBar

from railing_generator.presentation.viewport_widget import ViewportWidget


class MainWindow(QMainWindow):
    """
    Main application window for the Railing Infill Generator.

    Layout:
    - Menu bar with File, View, Help menus
    - Central viewport for rendering
    - Status bar for operation status
    """

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()

        # Window properties
        self.setWindowTitle("Untitled* - Railing Infill Generator")
        self.resize(1200, 800)

        # Create viewport as central widget
        self.viewport = ViewportWidget()
        self.setCentralWidget(self.viewport)

        # Create menu bar
        self._create_menu_bar()

        # Create status bar
        self._create_status_bar()

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

    def update_window_title(self, filename: str | None = None, modified: bool = False) -> None:
        """
        Update the window title with filename and modified status.

        Args:
            filename: Name of the current file, or None for "Untitled"
            modified: Whether the project has unsaved changes
        """
        if filename is None:
            title = "Untitled"
        else:
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
