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
    window._skip_close_confirmation = True  # Prevent dialog on close during tests
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


class TestMainWindowEditMenu:
    """Test Edit menu functionality."""

    def test_edit_menu_exists(self, main_window: MainWindow) -> None:
        """Test that Edit menu exists."""
        menu_bar = main_window.menuBar()
        assert menu_bar is not None

        menus = menu_bar.findChildren(type(menu_bar.addMenu("test")))
        menu_titles = [menu.title() for menu in menus if menu.title()]

        assert any("Edit" in title for title in menu_titles)

    def test_undo_action_exists(self, main_window: MainWindow) -> None:
        """Test that Undo action exists."""
        assert hasattr(main_window, "undo_action")
        assert main_window.undo_action is not None

    def test_redo_action_exists(self, main_window: MainWindow) -> None:
        """Test that Redo action exists."""
        assert hasattr(main_window, "redo_action")
        assert main_window.redo_action is not None

    def test_undo_action_initially_disabled(self, main_window: MainWindow) -> None:
        """Test that Undo action is initially disabled."""
        assert not main_window.undo_action.isEnabled()

    def test_redo_action_initially_disabled(self, main_window: MainWindow) -> None:
        """Test that Redo action is initially disabled."""
        assert not main_window.redo_action.isEnabled()

    def test_undo_action_has_shortcut(self, main_window: MainWindow) -> None:
        """Test that Undo action has Ctrl+Z shortcut."""
        from PySide6.QtGui import QKeySequence

        shortcut = main_window.undo_action.shortcut()
        expected = QKeySequence(QKeySequence.StandardKey.Undo)
        assert shortcut == expected

    def test_redo_action_has_shortcut(self, main_window: MainWindow) -> None:
        """Test that Redo action has Ctrl+Y shortcut."""
        from PySide6.QtGui import QKeySequence

        shortcut = main_window.redo_action.shortcut()
        expected = QKeySequence(QKeySequence.StandardKey.Redo)
        assert shortcut == expected

    def test_undo_available_enables_action(
        self, main_window: MainWindow, project_model: RailingProjectModel
    ) -> None:
        """Test that undo_available_changed signal enables/disables action."""
        # Initially disabled
        assert not main_window.undo_action.isEnabled()

        # Emit signal that undo is available
        main_window.manual_edit_controller.undo_available_changed.emit(True)

        # Action should be enabled
        assert main_window.undo_action.isEnabled()

        # Emit signal that undo is not available
        main_window.manual_edit_controller.undo_available_changed.emit(False)

        # Action should be disabled
        assert not main_window.undo_action.isEnabled()

    def test_redo_available_enables_action(
        self, main_window: MainWindow, project_model: RailingProjectModel
    ) -> None:
        """Test that redo_available_changed signal enables/disables action."""
        # Initially disabled
        assert not main_window.redo_action.isEnabled()

        # Emit signal that redo is available
        main_window.manual_edit_controller.redo_available_changed.emit(True)

        # Action should be enabled
        assert main_window.redo_action.isEnabled()

        # Emit signal that redo is not available
        main_window.manual_edit_controller.redo_available_changed.emit(False)

        # Action should be disabled
        assert not main_window.redo_action.isEnabled()

    def test_undo_action_calls_controller(
        self, main_window: MainWindow, project_model: RailingProjectModel
    ) -> None:
        """Test that triggering Undo action calls controller.undo()."""
        from shapely.geometry import LineString

        from railing_generator.domain.anchor_point import AnchorPoint
        from railing_generator.domain.railing_infill import RailingInfill
        from railing_generator.domain.rod import Rod

        # Set up infill with rod and anchors for editing
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
        project_model.set_railing_infill(infill)

        # Perform an edit to populate undo stack
        main_window.manual_edit_controller.select_anchor_at((0.0, 0.0))
        main_window.manual_edit_controller.reconnect_to_anchor_at((100.0, 0.0))

        # Undo should be available now
        assert main_window.undo_action.isEnabled()

        # Trigger undo action
        main_window.undo_action.trigger()

        # Undo should have been performed (undo stack should be empty now)
        assert not main_window.manual_edit_controller.can_undo

    def test_redo_action_calls_controller(
        self, main_window: MainWindow, project_model: RailingProjectModel
    ) -> None:
        """Test that triggering Redo action calls controller.redo()."""
        from shapely.geometry import LineString

        from railing_generator.domain.anchor_point import AnchorPoint
        from railing_generator.domain.railing_infill import RailingInfill
        from railing_generator.domain.rod import Rod

        # Set up infill with rod and anchors for editing
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
        project_model.set_railing_infill(infill)

        # Perform an edit and undo it
        main_window.manual_edit_controller.select_anchor_at((0.0, 0.0))
        main_window.manual_edit_controller.reconnect_to_anchor_at((100.0, 0.0))
        main_window.manual_edit_controller.undo()

        # Redo should be available now
        assert main_window.redo_action.isEnabled()

        # Trigger redo action
        main_window.redo_action.trigger()

        # Redo should have been performed (redo stack should be empty now)
        assert not main_window.manual_edit_controller.can_redo


class TestMainWindowFitnessDisplay:
    """Test fitness score display in status bar."""

    def _get_status_message(self, main_window: MainWindow) -> str:
        """Helper to get the current status bar message."""
        status_bar = main_window.statusBar()
        if status_bar is not None:
            return status_bar.currentMessage()
        return ""

    def test_status_bar_exists(self, main_window: MainWindow) -> None:
        """Test that status bar exists."""
        assert main_window.statusBar() is not None

    def test_status_bar_initially_ready(self, main_window: MainWindow) -> None:
        """Test that status bar initially shows 'Ready'."""
        assert self._get_status_message(main_window) == "Ready"

    def test_fitness_display_with_both_scores(self, main_window: MainWindow) -> None:
        """Test fitness display with both old and new scores."""
        from railing_generator.domain.fitness_update import FitnessUpdate

        # Emit fitness scores signal with FitnessUpdate
        main_window.manual_edit_controller.fitness_scores_updated.emit(
            FitnessUpdate(old_score=0.72, new_score=0.78, is_acceptable=True)
        )

        # Check text format in status bar
        text = self._get_status_message(main_window)
        assert "Fitness:" in text
        assert "0.72" in text
        assert "0.78" in text
        assert "→" in text
        assert "%" in text

    def test_fitness_display_shows_percentage_increase(self, main_window: MainWindow) -> None:
        """Test that fitness display shows positive percentage change."""
        from railing_generator.domain.fitness_update import FitnessUpdate

        main_window.manual_edit_controller.fitness_scores_updated.emit(
            FitnessUpdate(old_score=0.72, new_score=0.78, is_acceptable=True)
        )

        text = self._get_status_message(main_window)
        # 0.78 - 0.72 = 0.06, 0.06 / 0.72 = 8.33%
        assert "+" in text  # Positive change should have + sign

    def test_fitness_display_shows_percentage_decrease(self, main_window: MainWindow) -> None:
        """Test that fitness display shows negative percentage change."""
        from railing_generator.domain.fitness_update import FitnessUpdate

        main_window.manual_edit_controller.fitness_scores_updated.emit(
            FitnessUpdate(old_score=0.78, new_score=0.72, is_acceptable=True)
        )

        text = self._get_status_message(main_window)
        # Negative change should not have + sign (just -)
        assert "-" in text

    def test_fitness_display_with_only_new_score(self, main_window: MainWindow) -> None:
        """Test fitness display with only new score."""
        from railing_generator.domain.fitness_update import FitnessUpdate

        main_window.manual_edit_controller.fitness_scores_updated.emit(
            FitnessUpdate(old_score=None, new_score=0.85, is_acceptable=True)
        )

        text = self._get_status_message(main_window)
        assert "0.85" in text

    def test_fitness_display_with_only_old_score(self, main_window: MainWindow) -> None:
        """Test fitness display with only old score (new is None)."""
        from railing_generator.domain.fitness_update import FitnessUpdate

        main_window.manual_edit_controller.fitness_scores_updated.emit(
            FitnessUpdate(old_score=0.72, new_score=None, is_acceptable=None)
        )

        text = self._get_status_message(main_window)
        assert "0.72" in text
        assert "before edit" in text

    def test_fitness_display_unchanged_when_no_scores(self, main_window: MainWindow) -> None:
        """Test that status bar is unchanged when both scores are None."""
        from railing_generator.domain.fitness_update import FitnessUpdate

        # First show fitness
        main_window.manual_edit_controller.fitness_scores_updated.emit(
            FitnessUpdate(old_score=0.72, new_score=0.78, is_acceptable=True)
        )
        text_before = self._get_status_message(main_window)
        assert "Fitness:" in text_before

        # Emit None, None, None - should not change the message
        main_window.manual_edit_controller.fitness_scores_updated.emit(
            FitnessUpdate(old_score=None, new_score=None, is_acceptable=None)
        )
        text_after = self._get_status_message(main_window)
        # Message should remain unchanged (not cleared)
        assert text_after == text_before

    def test_fitness_display_shows_warning_when_not_acceptable(
        self, main_window: MainWindow
    ) -> None:
        """Test that fitness display shows warning when infill is not acceptable."""
        from railing_generator.domain.fitness_update import FitnessUpdate

        main_window.manual_edit_controller.fitness_scores_updated.emit(
            FitnessUpdate(old_score=0.72, new_score=0.78, is_acceptable=False)
        )

        text = self._get_status_message(main_window)
        assert "INVALID" in text
        assert "Fitness:" in text


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
