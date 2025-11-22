"""Tests for ApplicationController."""

from typing import TYPE_CHECKING

import pytest

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.shapes.staircase_railing_shape import (
    StaircaseRailingShapeParameters,
)

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


class TestApplicationController:
    """Test suite for ApplicationController."""

    @pytest.fixture
    def project_model(self, qtbot: "QtBot") -> RailingProjectModel:
        """Create a RailingProjectModel for testing."""
        return RailingProjectModel()

    @pytest.fixture
    def controller(self, project_model: RailingProjectModel) -> ApplicationController:
        """Create an ApplicationController for testing."""
        return ApplicationController(project_model)

    def test_initialization(
        self, controller: ApplicationController, project_model: RailingProjectModel
    ) -> None:
        """Test that controller is initialized with the project model."""
        # Assert
        assert controller.project_model is project_model

    def test_create_new_project(
        self, qtbot: "QtBot", controller: ApplicationController, project_model: RailingProjectModel
    ) -> None:
        """Test creating a new project resets the model."""
        # Arrange - Set some state in the model
        params = StaircaseRailingShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )
        project_model.set_railing_shape_type("staircase")
        project_model.set_railing_shape_parameters(params)

        # Verify state is set
        assert project_model.railing_shape_type == "staircase"
        assert project_model.railing_shape_parameters is not None

        # Act
        controller.create_new_project()

        # Assert - State should be cleared
        assert project_model.railing_shape_type is None
        assert project_model.railing_shape_parameters is None
        assert project_model.railing_frame is None
        assert project_model.project_modified is False

    def test_update_railing_shape_updates_model(
        self, qtbot: "QtBot", controller: ApplicationController, project_model: RailingProjectModel
    ) -> None:
        """Test that update_railing_shape updates the model correctly."""
        # Arrange
        params = StaircaseRailingShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )

        # Act
        controller.update_railing_shape("staircase", params)

        # Assert - Model should be updated
        assert project_model.railing_shape_type == "staircase"
        assert project_model.railing_shape_parameters == params
        assert project_model.railing_frame is not None
        assert isinstance(project_model.railing_frame, RailingFrame)
        assert project_model.project_modified is True

    def test_update_railing_shape_emits_signals(
        self, qtbot: "QtBot", controller: ApplicationController, project_model: RailingProjectModel
    ) -> None:
        """Test that update_railing_shape emits the expected signals."""
        # Arrange
        params = StaircaseRailingShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )

        # Track signal emissions
        shape_type_changed = False
        shape_params_changed = False
        frame_updated_count = 0
        final_frame: object = None

        def on_shape_type_changed(shape_type: str) -> None:
            nonlocal shape_type_changed
            shape_type_changed = True
            assert shape_type == "staircase"

        def on_shape_params_changed(shape_params: object) -> None:
            nonlocal shape_params_changed
            shape_params_changed = True
            assert shape_params == params

        def on_frame_updated(frame: object) -> None:
            nonlocal frame_updated_count, final_frame
            frame_updated_count += 1
            final_frame = frame

        project_model.railing_shape_type_changed.connect(on_shape_type_changed)
        project_model.railing_shape_parameters_changed.connect(on_shape_params_changed)
        project_model.railing_frame_updated.connect(on_frame_updated)

        # Act
        controller.update_railing_shape("staircase", params)

        # Assert - All signals should have been emitted
        assert shape_type_changed
        assert shape_params_changed
        # Frame updated signal is emitted twice: once to clear (None), once to set the new frame
        assert frame_updated_count >= 1
        # The final frame should be a valid RailingFrame
        assert isinstance(final_frame, RailingFrame)

    def test_update_railing_shape_generates_valid_frame(
        self, qtbot: "QtBot", controller: ApplicationController, project_model: RailingProjectModel
    ) -> None:
        """Test that update_railing_shape generates a valid frame with rods."""
        # Arrange
        params = StaircaseRailingShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )

        # Act
        controller.update_railing_shape("staircase", params)

        # Assert - Frame should have rods and boundary
        frame = project_model.railing_frame
        assert frame is not None
        assert len(frame.rods) > 0
        assert frame.boundary is not None
        assert frame.boundary.is_valid
        assert not frame.boundary.is_empty

    def test_update_railing_shape_with_invalid_type_raises_error(
        self, qtbot: "QtBot", controller: ApplicationController
    ) -> None:
        """Test that update_railing_shape with invalid type raises ValueError."""
        # Arrange
        params = StaircaseRailingShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Unknown shape type"):
            controller.update_railing_shape("invalid_type", params)

    def test_update_railing_shape_clears_infill(
        self, qtbot: "QtBot", controller: ApplicationController, project_model: RailingProjectModel
    ) -> None:
        """Test that updating shape clears any existing infill."""
        # Arrange - Set up initial shape and mock infill
        params = StaircaseRailingShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )
        controller.update_railing_shape("staircase", params)

        # Manually set infill (simulating a previous generation)
        from railing_generator.domain.railing_infill import RailingInfill

        mock_infill = RailingInfill(rods=[])
        project_model.set_railing_infill(mock_infill)
        assert project_model.railing_infill is not None

        # Act - Update shape again
        new_params = StaircaseRailingShapeParameters(
            post_length_cm=200.0,  # Different parameters
            stair_width_cm=300.0,
            stair_height_cm=300.0,
            num_steps=12,
            frame_weight_per_meter_kg_m=0.5,
        )
        controller.update_railing_shape("staircase", new_params)

        # Assert - Infill should be cleared
        assert project_model.railing_infill is None
