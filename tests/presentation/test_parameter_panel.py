"""Tests for ParameterPanel."""

from typing import TYPE_CHECKING

import pytest

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.presentation.parameter_panel import ParameterPanel

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


class TestParameterPanel:
    """Test suite for ParameterPanel."""

    @pytest.fixture
    def project_model(self, qtbot: "QtBot") -> RailingProjectModel:
        """Create a RailingProjectModel for testing."""
        return RailingProjectModel()

    @pytest.fixture
    def controller(self, project_model: RailingProjectModel) -> ApplicationController:
        """Create an ApplicationController for testing."""
        return ApplicationController(project_model)

    @pytest.fixture
    def panel(
        self, qtbot: "QtBot", project_model: RailingProjectModel, controller: ApplicationController
    ) -> ParameterPanel:
        """Create a ParameterPanel for testing."""
        panel = ParameterPanel(project_model, controller)
        qtbot.addWidget(panel)
        return panel

    def test_initialization(
        self, panel: ParameterPanel, project_model: RailingProjectModel
    ) -> None:
        """Test that panel is initialized correctly."""
        assert panel.project_model is project_model
        assert panel.shape_type_combo is not None
        assert panel.update_shape_button is not None

    def test_shape_type_combo_has_options(self, panel: ParameterPanel) -> None:
        """Test that shape type combo box has available shape types."""
        assert panel.shape_type_combo.count() >= 2
        # Check that staircase and rectangular are available
        types = [panel.shape_type_combo.itemData(i) for i in range(panel.shape_type_combo.count())]
        assert "staircase" in types
        assert "rectangular" in types

    def test_initial_shape_is_staircase(self, panel: ParameterPanel) -> None:
        """Test that initial shape type is staircase."""
        current_type = panel.shape_type_combo.currentData()
        assert current_type == "staircase"

    def test_staircase_parameters_displayed(self, panel: ParameterPanel) -> None:
        """Test that staircase parameters are displayed initially."""
        # Select staircase (should already be selected)
        panel.shape_type_combo.setCurrentIndex(0)
        
        # Check that current parameter widget is StaircaseParameterWidget
        from railing_generator.presentation.shape_parameter_widget import StaircaseParameterWidget
        
        assert panel.current_param_widget is not None
        assert isinstance(panel.current_param_widget, StaircaseParameterWidget)

    def test_rectangular_parameters_displayed(self, panel: ParameterPanel) -> None:
        """Test that rectangular parameters are displayed when selected."""
        # Find rectangular index
        rect_index = -1
        for i in range(panel.shape_type_combo.count()):
            if panel.shape_type_combo.itemData(i) == "rectangular":
                rect_index = i
                break
        
        assert rect_index >= 0
        
        # Select rectangular
        panel.shape_type_combo.setCurrentIndex(rect_index)
        
        # Check that current parameter widget is RectangularParameterWidget
        from railing_generator.presentation.shape_parameter_widget import RectangularParameterWidget
        
        assert panel.current_param_widget is not None
        assert isinstance(panel.current_param_widget, RectangularParameterWidget)

    def test_switching_shape_clears_old_parameters(self, panel: ParameterPanel) -> None:
        """Test that switching shape type clears old parameter widgets."""
        from railing_generator.presentation.shape_parameter_widget import (
            RectangularParameterWidget,
            StaircaseParameterWidget,
        )
        
        # Start with staircase
        assert isinstance(panel.current_param_widget, StaircaseParameterWidget)
        
        # Switch to rectangular
        rect_index = -1
        for i in range(panel.shape_type_combo.count()):
            if panel.shape_type_combo.itemData(i) == "rectangular":
                rect_index = i
                break
        panel.shape_type_combo.setCurrentIndex(rect_index)
        
        # Should now have rectangular widget
        assert isinstance(panel.current_param_widget, RectangularParameterWidget)

    def test_update_shape_button_updates_model(
        self,
        qtbot: "QtBot",
        panel: ParameterPanel,
        project_model: RailingProjectModel,
    ) -> None:
        """Test that clicking Update Shape button updates the model."""
        from railing_generator.presentation.shape_parameter_widget import StaircaseParameterWidget
        from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox
        
        # Arrange - Set staircase parameters
        assert isinstance(panel.current_param_widget, StaircaseParameterWidget)
        widget = panel.current_param_widget
        
        # Access widgets via field_widgets dictionary
        post_length = widget.field_widgets["post_length_cm"]
        assert isinstance(post_length, QDoubleSpinBox)
        post_length.setValue(200.0)
        
        stair_width = widget.field_widgets["stair_width_cm"]
        assert isinstance(stair_width, QDoubleSpinBox)
        stair_width.setValue(300.0)
        
        stair_height = widget.field_widgets["stair_height_cm"]
        assert isinstance(stair_height, QDoubleSpinBox)
        stair_height.setValue(300.0)
        
        num_steps = widget.field_widgets["num_steps"]
        assert isinstance(num_steps, QSpinBox)
        num_steps.setValue(12)
        
        frame_weight = widget.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)
        frame_weight.setValue(0.6)
        
        # Act - Click update button
        panel.update_shape_button.click()
        
        # Wait for processing
        qtbot.wait(100)
        
        # Assert - Model should be updated
        assert project_model.railing_shape_type == "staircase"
        assert project_model.railing_frame is not None
        assert len(project_model.railing_frame.rods) > 0

    def test_update_rectangular_shape_updates_model(
        self,
        qtbot: "QtBot",
        panel: ParameterPanel,
        project_model: RailingProjectModel,
    ) -> None:
        """Test that updating rectangular shape updates the model."""
        from railing_generator.presentation.shape_parameter_widget import RectangularParameterWidget
        from PySide6.QtWidgets import QDoubleSpinBox
        
        # Arrange - Switch to rectangular
        rect_index = -1
        for i in range(panel.shape_type_combo.count()):
            if panel.shape_type_combo.itemData(i) == "rectangular":
                rect_index = i
                break
        panel.shape_type_combo.setCurrentIndex(rect_index)
        
        # Set rectangular parameters
        assert isinstance(panel.current_param_widget, RectangularParameterWidget)
        widget = panel.current_param_widget
        
        width = widget.field_widgets["width_cm"]
        assert isinstance(width, QDoubleSpinBox)
        width.setValue(250.0)
        
        height = widget.field_widgets["height_cm"]
        assert isinstance(height, QDoubleSpinBox)
        height.setValue(120.0)
        
        frame_weight = widget.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)
        frame_weight.setValue(0.7)
        
        # Act - Click update button
        panel.update_shape_button.click()
        
        # Wait for processing
        qtbot.wait(100)
        
        # Assert - Model should be updated
        assert project_model.railing_shape_type == "rectangular"
        assert project_model.railing_frame is not None
        assert len(project_model.railing_frame.rods) == 4  # Rectangular has 4 sides

    def test_default_values_loaded(self, panel: ParameterPanel) -> None:
        """Test that default values are loaded from config."""
        from railing_generator.presentation.shape_parameter_widget import StaircaseParameterWidget
        from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox
        
        # Check staircase defaults
        assert isinstance(panel.current_param_widget, StaircaseParameterWidget)
        widget = panel.current_param_widget
        
        post_length = widget.field_widgets["post_length_cm"]
        assert isinstance(post_length, QDoubleSpinBox)
        assert post_length.value() == 150.0
        
        stair_width = widget.field_widgets["stair_width_cm"]
        assert isinstance(stair_width, QDoubleSpinBox)
        assert stair_width.value() == 280.0
        
        stair_height = widget.field_widgets["stair_height_cm"]
        assert isinstance(stair_height, QDoubleSpinBox)
        assert stair_height.value() == 280.0
        
        num_steps = widget.field_widgets["num_steps"]
        assert isinstance(num_steps, QSpinBox)
        assert num_steps.value() == 10
        
        frame_weight = widget.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)
        assert frame_weight.value() == 0.5

    def test_parameter_ranges(self, panel: ParameterPanel) -> None:
        """Test that parameter spin boxes have appropriate ranges."""
        from railing_generator.presentation.shape_parameter_widget import StaircaseParameterWidget
        from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox
        
        # Check staircase parameter ranges
        assert isinstance(panel.current_param_widget, StaircaseParameterWidget)
        widget = panel.current_param_widget
        
        post_length = widget.field_widgets["post_length_cm"]
        assert isinstance(post_length, QDoubleSpinBox)
        assert post_length.minimum() > 0
        
        stair_width = widget.field_widgets["stair_width_cm"]
        assert isinstance(stair_width, QDoubleSpinBox)
        assert stair_width.minimum() > 0
        
        stair_height = widget.field_widgets["stair_height_cm"]
        assert isinstance(stair_height, QDoubleSpinBox)
        assert stair_height.minimum() > 0
        
        num_steps = widget.field_widgets["num_steps"]
        assert isinstance(num_steps, QSpinBox)
        assert num_steps.minimum() >= 1
        assert num_steps.maximum() <= 50
        
        frame_weight = widget.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)
        assert frame_weight.minimum() > 0
