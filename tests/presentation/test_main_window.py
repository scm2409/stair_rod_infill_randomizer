"""Tests for MainWindow."""

import pytest

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.presentation.main_window import MainWindow


@pytest.fixture
def project_model() -> RailingProjectModel:
    """Create a RailingProjectModel for testing."""
    return RailingProjectModel()


@pytest.fixture
def controller(project_model: RailingProjectModel) -> ApplicationController:
    """Create an ApplicationController for testing."""
    return ApplicationController(project_model)


@pytest.fixture
def main_window(qtbot, project_model: RailingProjectModel, controller: ApplicationController):  # type: ignore[no-untyped-def]
    """Create a MainWindow for testing."""
    window = MainWindow(project_model, controller)
    qtbot.addWidget(window)
    return window


class TestMainWindowCreation:
    """Test main window creation and initialization."""

    def test_create_main_window(self, main_window: MainWindow) -> None:
        """Test that main window is created successfully."""
        assert main_window is not None

    def test_window_has_viewport(self, main_window: MainWindow) -> None:
        """Test that main window has a viewport."""
        assert main_window.viewport is not None
        assert main_window.centralWidget() is not None

    def test_window_has_parameter_panel(self, main_window: MainWindow) -> None:
        """Test that main window has a parameter panel."""
        assert main_window.parameter_panel is not None

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

    def test_color_infill_layers_action_exists(self, main_window: MainWindow) -> None:
        """Test that 'Color Infill Layers by Layer' action exists in View menu."""
        assert hasattr(main_window, "color_infill_layers_action")
        assert main_window.color_infill_layers_action is not None

    def test_color_infill_layers_action_is_checkable(self, main_window: MainWindow) -> None:
        """Test that 'Color Infill Layers by Layer' action is checkable."""
        assert main_window.color_infill_layers_action.isCheckable()

    def test_color_infill_layers_action_initial_state(self, main_window: MainWindow) -> None:
        """Test that 'Color Infill Layers by Layer' action starts checked (colored mode)."""
        assert main_window.color_infill_layers_action.isChecked()

    def test_color_infill_layers_action_triggers_model_toggle(
        self, main_window: MainWindow, project_model: RailingProjectModel
    ) -> None:
        """Test that triggering the action toggles the model state."""
        # Initial state is True (colored)
        assert project_model.infill_layers_colored_by_layer is True

        # Trigger the action
        main_window.color_infill_layers_action.trigger()

        # Model should now be False (monochrome)
        assert project_model.infill_layers_colored_by_layer is False

        # Trigger again
        main_window.color_infill_layers_action.trigger()

        # Model should be back to True (colored)
        assert project_model.infill_layers_colored_by_layer is True

    def test_model_change_updates_action_checkbox(
        self, main_window: MainWindow, project_model: RailingProjectModel
    ) -> None:
        """Test that changing model state updates the action checkbox."""
        # Initial state is True (colored)
        assert main_window.color_infill_layers_action.isChecked()

        # Change model directly (not via action)
        project_model.set_infill_layers_colored_by_layer(False)

        # Action checkbox should update
        assert not main_window.color_infill_layers_action.isChecked()

        # Change back
        project_model.set_infill_layers_colored_by_layer(True)

        # Action checkbox should update again
        assert main_window.color_infill_layers_action.isChecked()


class TestMainWindowTitleUpdate:
    """Test window title update functionality via model."""

    def test_update_title_with_filename(
        self, main_window: MainWindow, project_model: RailingProjectModel
    ) -> None:
        """Test updating window title with a filename via model."""
        from pathlib import Path

        # Update model with file path (not modified)
        project_model.set_project_file_path(Path("project.rig.zip"))
        project_model.mark_project_saved()

        assert "project.rig.zip" in main_window.windowTitle()
        assert "Railing Infill Generator" in main_window.windowTitle()
        assert "*" not in main_window.windowTitle().split(" - ")[0]

    def test_update_title_with_modified_flag(
        self, main_window: MainWindow, project_model: RailingProjectModel
    ) -> None:
        """Test updating window title with modified flag via model."""
        from pathlib import Path

        # Update model with file path
        project_model.set_project_file_path(Path("project.rig.zip"))
        # Mark as modified
        project_model._mark_modified()

        assert "project.rig.zip*" in main_window.windowTitle()

    def test_update_title_untitled(
        self, main_window: MainWindow, project_model: RailingProjectModel
    ) -> None:
        """Test updating window title with no filename via model."""
        # Model starts with no file path and modified=False
        # Mark as modified
        project_model._mark_modified()

        assert "Untitled*" in main_window.windowTitle()

    def test_update_title_untitled_not_modified(
        self, main_window: MainWindow, project_model: RailingProjectModel
    ) -> None:
        """Test updating window title with no filename and not modified via model."""
        # Model starts with no file path
        # Mark as saved (not modified)
        project_model.mark_project_saved()

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

    def test_progress_update_with_fitness(self, main_window: MainWindow) -> None:
        """Test status bar update during generation with fitness score."""
        from railing_generator.domain.generation_progress import GenerationProgress
        from railing_generator.domain.railing_infill import RailingInfill
        from railing_generator.domain.rod import Rod
        from shapely.geometry import LineString

        # Create progress object
        progress = GenerationProgress(iteration=42, elapsed_sec=12.3)

        # Create infill with fitness score (single source of truth for fitness)
        rod = Rod(
            geometry=LineString([(0.0, 0.0), (100.0, 0.0)]),
            start_cut_angle_deg=90.0,
            end_cut_angle_deg=90.0,
            weight_kg_m=0.5,
        )
        infill = RailingInfill(
            rods=[rod],
            fitness_score=0.8567,
            iteration_count=42,
            duration_sec=12.3,
            anchor_points=[],
            is_complete=True,
        )
        main_window.project_model.set_railing_infill(infill)

        main_window._on_progress_updated(progress)

        status_bar = main_window.statusBar()
        assert status_bar is not None
        message = status_bar.currentMessage()
        assert "Iteration 42" in message
        assert "Fitness 0.8567" in message
        assert "Elapsed 12.3s" in message

    def test_progress_update_without_fitness(self, main_window: MainWindow) -> None:
        """Test status bar update during generation without fitness score."""
        from railing_generator.domain.generation_progress import GenerationProgress

        # Create progress object
        progress = GenerationProgress(iteration=10, elapsed_sec=5.7)

        # No infill set, so fitness will be None
        main_window._on_progress_updated(progress)

        status_bar = main_window.statusBar()
        assert status_bar is not None
        message = status_bar.currentMessage()
        assert "Iteration 10" in message
        assert "Elapsed 5.7s" in message
        assert "Fitness" not in message

    def test_progress_update_formats_correctly(self, main_window: MainWindow) -> None:
        """Test that progress updates are formatted with separators."""
        from railing_generator.domain.generation_progress import GenerationProgress
        from railing_generator.domain.railing_infill import RailingInfill
        from railing_generator.domain.rod import Rod
        from shapely.geometry import LineString

        # Create progress object
        progress = GenerationProgress(iteration=100, elapsed_sec=45.6)

        # Create infill with fitness score
        rod = Rod(
            geometry=LineString([(0.0, 0.0), (100.0, 0.0)]),
            start_cut_angle_deg=90.0,
            end_cut_angle_deg=90.0,
            weight_kg_m=0.5,
        )
        infill = RailingInfill(
            rods=[rod],
            fitness_score=0.9234,
            iteration_count=100,
            duration_sec=45.6,
            anchor_points=[],
            is_complete=True,
        )
        main_window.project_model.set_railing_infill(infill)

        main_window._on_progress_updated(progress)

        status_bar = main_window.statusBar()
        assert status_bar is not None
        message = status_bar.currentMessage()
        # Check that parts are separated by " | "
        assert " | " in message
        parts = message.split(" | ")
        assert len(parts) == 3  # iteration, fitness, elapsed

    def test_generation_completed_shows_final_stats(self, main_window: MainWindow) -> None:
        """Test that completion message shows final iteration, fitness, and elapsed time."""
        from railing_generator.domain.generation_progress import GenerationProgress
        from railing_generator.domain.railing_infill import RailingInfill
        from railing_generator.domain.rod import Rod
        from shapely.geometry import LineString

        # Simulate progress updates
        progress = GenerationProgress(iteration=50, elapsed_sec=12.3)
        main_window.project_model.set_generation_progress(progress)

        # Set RailingInfill with fitness score (single source of truth)
        rod = Rod(
            geometry=LineString([(0.0, 0.0), (100.0, 0.0)]),
            start_cut_angle_deg=90.0,
            end_cut_angle_deg=90.0,
            weight_kg_m=0.5,
        )
        infill = RailingInfill(
            rods=[rod],
            fitness_score=0.8567,
            iteration_count=50,
            duration_sec=12.3,
            anchor_points=[],
            is_complete=True,
        )
        main_window.project_model.set_railing_infill(infill)

        # Simulate completion
        main_window._on_generation_completed(None)

        status_bar = main_window.statusBar()
        assert status_bar is not None
        message = status_bar.currentMessage()
        assert "Completed" in message
        assert "Iteration 50" in message
        assert "0.8567" in message  # Fitness from RailingInfill
        assert "12.3s" in message

    def test_generation_failed_shows_final_stats(self, main_window: MainWindow) -> None:
        """Test that failure message shows final iteration, fitness, and elapsed time."""
        from railing_generator.domain.generation_progress import GenerationProgress
        from railing_generator.domain.railing_infill import RailingInfill
        from railing_generator.domain.rod import Rod
        from shapely.geometry import LineString

        # Simulate progress updates
        progress = GenerationProgress(iteration=25, elapsed_sec=6.7)
        main_window.project_model.set_generation_progress(progress)

        # Set RailingInfill with fitness score (single source of truth)
        rod = Rod(
            geometry=LineString([(0.0, 0.0), (100.0, 0.0)]),
            start_cut_angle_deg=90.0,
            end_cut_angle_deg=90.0,
            weight_kg_m=0.5,
        )
        infill = RailingInfill(
            rods=[rod],
            fitness_score=0.4321,
            iteration_count=25,
            duration_sec=6.7,
            anchor_points=[],
            is_complete=True,
        )
        main_window.project_model.set_railing_infill(infill)

        # Simulate failure
        main_window._on_generation_failed("Test error")

        status_bar = main_window.statusBar()
        assert status_bar is not None
        message = status_bar.currentMessage()
        assert "Failed" in message
        assert "Iteration 25" in message
        assert "0.4321" in message  # Fitness from RailingInfill
        assert "6.7s" in message
