"""Tests for MainWindow."""

import pytest

from railing_generator.presentation.main_window import MainWindow


@pytest.fixture
def main_window(qtbot):  # type: ignore[no-untyped-def]
    """Create a MainWindow for testing."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window


class TestMainWindowCreation:
    """Test main window creation and initialization."""

    def test_create_main_window(self, main_window: MainWindow) -> None:
        """Test that main window is created successfully."""
        assert main_window is not None

    def test_window_has_viewport(self, main_window: MainWindow) -> None:
        """Test that main window has a viewport as central widget."""
        assert main_window.viewport is not None
        assert main_window.centralWidget() == main_window.viewport

    def test_window_has_menu_bar(self, main_window: MainWindow) -> None:
        """Test that main window has a menu bar."""
        menu_bar = main_window.menuBar()
        assert menu_bar is not None

    def test_window_has_status_bar(self, main_window: MainWindow) -> None:
        """Test that main window has a status bar."""
        status_bar = main_window.statusBar()
        assert status_bar is not None

    def test_initial_window_title(self, main_window: MainWindow) -> None:
        """Test that initial window title is correct."""
        assert "Untitled*" in main_window.windowTitle()
        assert "Railing Infill Generator" in main_window.windowTitle()

    def test_initial_status_message(self, main_window: MainWindow) -> None:
        """Test that initial status message is 'Ready'."""
        status_bar = main_window.statusBar()
        assert status_bar is not None
        assert status_bar.currentMessage() == "Ready"


class TestMainWindowMenus:
    """Test main window menu structure."""

    def test_file_menu_exists(self, main_window: MainWindow) -> None:
        """Test that File menu exists."""
        menu_bar = main_window.menuBar()
        assert menu_bar is not None

        menus = menu_bar.findChildren(type(menu_bar.addMenu("test")))
        menu_titles = [menu.title() for menu in menus if menu.title()]

        assert any("File" in title for title in menu_titles)

    def test_view_menu_exists(self, main_window: MainWindow) -> None:
        """Test that View menu exists."""
        menu_bar = main_window.menuBar()
        assert menu_bar is not None

        menus = menu_bar.findChildren(type(menu_bar.addMenu("test")))
        menu_titles = [menu.title() for menu in menus if menu.title()]

        assert any("View" in title for title in menu_titles)

    def test_help_menu_exists(self, main_window: MainWindow) -> None:
        """Test that Help menu exists."""
        menu_bar = main_window.menuBar()
        assert menu_bar is not None

        menus = menu_bar.findChildren(type(menu_bar.addMenu("test")))
        menu_titles = [menu.title() for menu in menus if menu.title()]

        assert any("Help" in title for title in menu_titles)


class TestMainWindowTitleUpdate:
    """Test window title update functionality."""

    def test_update_title_with_filename(self, main_window: MainWindow) -> None:
        """Test updating window title with a filename."""
        main_window.update_window_title("project.rig.zip", modified=False)

        assert "project.rig.zip" in main_window.windowTitle()
        assert "Railing Infill Generator" in main_window.windowTitle()
        assert "*" not in main_window.windowTitle().split(" - ")[0]

    def test_update_title_with_modified_flag(self, main_window: MainWindow) -> None:
        """Test updating window title with modified flag."""
        main_window.update_window_title("project.rig.zip", modified=True)

        assert "project.rig.zip*" in main_window.windowTitle()

    def test_update_title_untitled(self, main_window: MainWindow) -> None:
        """Test updating window title with no filename."""
        main_window.update_window_title(None, modified=True)

        assert "Untitled*" in main_window.windowTitle()

    def test_update_title_untitled_not_modified(self, main_window: MainWindow) -> None:
        """Test updating window title with no filename and not modified."""
        main_window.update_window_title(None, modified=False)

        title = main_window.windowTitle()
        assert "Untitled" in title
        assert "Untitled*" not in title


class TestMainWindowStatusUpdate:
    """Test status bar update functionality."""

    def test_update_status_message(self, main_window: MainWindow) -> None:
        """Test updating status bar message."""
        main_window.update_status("Generating...")

        status_bar = main_window.statusBar()
        assert status_bar is not None
        assert status_bar.currentMessage() == "Generating..."

    def test_update_status_multiple_times(self, main_window: MainWindow) -> None:
        """Test updating status bar message multiple times."""
        main_window.update_status("Loading...")
        main_window.update_status("Ready")

        status_bar = main_window.statusBar()
        assert status_bar is not None
        assert status_bar.currentMessage() == "Ready"
