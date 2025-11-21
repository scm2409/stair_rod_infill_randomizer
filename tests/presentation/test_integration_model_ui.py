"""Integration tests for RailingProjectModel and UI components."""

import pytest
from pytestqt.qtbot import QtBot

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.shapes.staircase_railing_shape import (
    StaircaseRailingShapeParameters,
)
from railing_generator.presentation.main_window import MainWindow
from railing_generator.presentation.viewport_widget import ViewportWidget


@pytest.fixture
def project_model() -> RailingProjectModel:
    """Create a RailingProjectModel for testing."""
    return RailingProjectModel()


@pytest.fixture
def controller(project_model: RailingProjectModel) -> ApplicationController:
    """Create an ApplicationController for testing."""
    return ApplicationController(project_model)


@pytest.fixture
def viewport(qtbot, project_model: RailingProjectModel):  # type: ignore[no-untyped-def]
    """Create a ViewportWidget for testing."""
    widget = ViewportWidget(project_model)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def main_window(qtbot, project_model: RailingProjectModel, controller: ApplicationController):  # type: ignore[no-untyped-def]
    """Create a MainWindow for testing."""
    window = MainWindow(project_model, controller)
    qtbot.addWidget(window)
    return window


class TestControllerUpdatesModel:
    """Test that controller updates the model correctly."""

    def test_update_railing_shape_updates_model_frame(
        self, controller: ApplicationController, project_model: RailingProjectModel
    ) -> None:
        """Test that updating shape via controller updates the model's frame."""
        # Initially no frame
        assert project_model.railing_frame is None

        # Update shape via controller
        params = StaircaseRailingShapeParameters(
            post_length_cm=120.0,
            stair_width_cm=280.0,
            stair_height_cm=150.0,
            num_steps=9,
            frame_weight_per_meter_kg_m=0.5,
        )
        controller.update_railing_shape("staircase", params)

        # Model should now have a frame
        assert project_model.railing_frame is not None
        assert project_model.railing_frame.rod_count > 0

    def test_update_railing_shape_updates_model_type(
        self, controller: ApplicationController, project_model: RailingProjectModel
    ) -> None:
        """Test that updating shape via controller updates the model's shape type."""
        # Initially no shape type
        assert project_model.railing_shape_type is None

        # Update shape via controller
        params = StaircaseRailingShapeParameters(
            post_length_cm=120.0,
            stair_width_cm=280.0,
            stair_height_cm=150.0,
            num_steps=9,
            frame_weight_per_meter_kg_m=0.5,
        )
        controller.update_railing_shape("staircase", params)

        # Model should now have shape type
        assert project_model.railing_shape_type == "staircase"

    def test_update_railing_shape_marks_project_modified(
        self, controller: ApplicationController, project_model: RailingProjectModel
    ) -> None:
        """Test that updating shape via controller marks project as modified."""
        # Initially not modified
        assert not project_model.project_modified

        # Update shape via controller
        params = StaircaseRailingShapeParameters(
            post_length_cm=120.0,
            stair_width_cm=280.0,
            stair_height_cm=150.0,
            num_steps=9,
            frame_weight_per_meter_kg_m=0.5,
        )
        controller.update_railing_shape("staircase", params)

        # Project should be marked as modified
        assert project_model.project_modified


class TestModelNotifiesViewport:
    """Test that model notifies viewport of changes."""

    def test_viewport_receives_frame_update_signal(
        self, qtbot: QtBot, viewport: ViewportWidget, project_model: RailingProjectModel
    ) -> None:
        """Test that viewport receives signal when frame is updated."""
        # Track signal emissions
        signal_received = []

        def on_signal(frame):  # type: ignore[no-untyped-def]
            signal_received.append(frame)

        project_model.railing_frame_updated.connect(on_signal)

        # Update frame via model
        params = StaircaseRailingShapeParameters(
            post_length_cm=120.0,
            stair_width_cm=280.0,
            stair_height_cm=150.0,
            num_steps=9,
            frame_weight_per_meter_kg_m=0.5,
        )
        from railing_generator.domain.shapes.staircase_railing_shape import (
            StaircaseRailingShape,
        )

        shape = StaircaseRailingShape(params)
        frame = shape.generate_frame()
        project_model.set_railing_frame(frame)

        # Signal should have been emitted
        assert len(signal_received) == 1
        assert signal_received[0] == frame

    def test_viewport_renders_frame_when_model_updates(
        self, viewport: ViewportWidget, controller: ApplicationController
    ) -> None:
        """Test that viewport renders frame when model is updated via controller."""
        # Initially no items in scene
        scene = viewport.scene()
        assert scene is not None
        initial_item_count = len(scene.items())

        # Update shape via controller (which updates model, which notifies viewport)
        params = StaircaseRailingShapeParameters(
            post_length_cm=120.0,
            stair_width_cm=280.0,
            stair_height_cm=150.0,
            num_steps=9,
            frame_weight_per_meter_kg_m=0.5,
        )
        controller.update_railing_shape("staircase", params)

        # Viewport should now have items (frame rods rendered)
        assert len(scene.items()) > initial_item_count


class TestModelNotifiesMainWindow:
    """Test that model notifies main window of changes."""

    def test_main_window_receives_modified_signal(
        self, qtbot: QtBot, main_window: MainWindow, project_model: RailingProjectModel
    ) -> None:
        """Test that main window receives signal when project is modified."""
        # Track signal emissions
        signal_received = []

        def on_signal(modified: bool) -> None:
            signal_received.append(modified)

        project_model.project_modified_changed.connect(on_signal)

        # Update frame via model (marks as modified)
        params = StaircaseRailingShapeParameters(
            post_length_cm=120.0,
            stair_width_cm=280.0,
            stair_height_cm=150.0,
            num_steps=9,
            frame_weight_per_meter_kg_m=0.5,
        )
        from railing_generator.domain.shapes.staircase_railing_shape import (
            StaircaseRailingShape,
        )

        shape = StaircaseRailingShape(params)
        frame = shape.generate_frame()
        project_model.set_railing_frame(frame)

        # Signal should have been emitted
        assert len(signal_received) == 1
        assert signal_received[0] is True

    def test_main_window_updates_title_when_model_changes(
        self, main_window: MainWindow, controller: ApplicationController
    ) -> None:
        """Test that main window updates title when model changes via controller."""
        # Initially title shows "Untitled*"
        assert "Untitled*" in main_window.windowTitle()

        # Update shape via controller (marks as modified)
        params = StaircaseRailingShapeParameters(
            post_length_cm=120.0,
            stair_width_cm=280.0,
            stair_height_cm=150.0,
            num_steps=9,
            frame_weight_per_meter_kg_m=0.5,
        )
        controller.update_railing_shape("staircase", params)

        # Title should still show modified flag
        assert "*" in main_window.windowTitle()
        assert "Railing Infill Generator" in main_window.windowTitle()


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow from controller to UI."""

    def test_complete_workflow_controller_to_ui(
        self,
        main_window: MainWindow,
        controller: ApplicationController,
        project_model: RailingProjectModel,
    ) -> None:
        """Test complete workflow: controller updates model, model notifies UI."""
        # Initial state
        assert project_model.railing_frame is None
        assert not project_model.project_modified

        # User action: Update shape via controller
        params = StaircaseRailingShapeParameters(
            post_length_cm=120.0,
            stair_width_cm=280.0,
            stair_height_cm=150.0,
            num_steps=9,
            frame_weight_per_meter_kg_m=0.5,
        )
        controller.update_railing_shape("staircase", params)

        # Verify model state
        assert project_model.railing_frame is not None
        assert project_model.railing_shape_type == "staircase"
        assert project_model.project_modified

        # Verify UI state (viewport has rendered items)
        viewport = main_window.viewport
        scene = viewport.scene()
        assert scene is not None
        assert len(scene.items()) > 0

        # Verify window title reflects modified state
        assert "*" in main_window.windowTitle()
