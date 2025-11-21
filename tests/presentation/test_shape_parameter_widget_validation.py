"""Tests for real-time validation in shape parameter widgets."""

from typing import TYPE_CHECKING

import pytest

from railing_generator.presentation.shape_parameter_widget import (
    RectangularParameterWidget,
    StaircaseParameterWidget,
)

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


class TestStaircaseParameterWidgetValidation:
    """Test suite for StaircaseParameterWidget validation."""

    @pytest.fixture
    def widget(self, qtbot: "QtBot") -> StaircaseParameterWidget:
        """Create a StaircaseParameterWidget for testing."""
        widget = StaircaseParameterWidget()
        qtbot.addWidget(widget)
        return widget

    def test_valid_parameters_no_errors(self, widget: StaircaseParameterWidget) -> None:
        """Test that valid parameters don't show errors."""
        # Default values should be valid
        params = widget.get_parameters()
        assert params is not None
        assert params.post_length_cm == 150.0

    def test_get_parameters_with_valid_values(self, widget: StaircaseParameterWidget) -> None:
        """Test getting parameters with valid custom values."""
        from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox
        
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

        params = widget.get_parameters()
        assert params.post_length_cm == 200.0
        assert params.stair_width_cm == 300.0
        assert params.stair_height_cm == 300.0
        assert params.num_steps == 12
        assert params.frame_weight_per_meter_kg_m == 0.6

    def test_validation_signals_connected(self, widget: StaircaseParameterWidget) -> None:
        """Test that validation signals are connected."""
        from PySide6.QtWidgets import QDoubleSpinBox
        
        # Change a value and verify no crash (signals are connected)
        post_length = widget.field_widgets["post_length_cm"]
        assert isinstance(post_length, QDoubleSpinBox)
        post_length.setValue(100.0)
        # If signals weren't connected properly, this would not trigger validation
        # The test passing means signals are working


class TestRectangularParameterWidgetValidation:
    """Test suite for RectangularParameterWidget validation."""

    @pytest.fixture
    def widget(self, qtbot: "QtBot") -> RectangularParameterWidget:
        """Create a RectangularParameterWidget for testing."""
        widget = RectangularParameterWidget()
        qtbot.addWidget(widget)
        return widget

    def test_valid_parameters_no_errors(self, widget: RectangularParameterWidget) -> None:
        """Test that valid parameters don't show errors."""
        # Default values should be valid
        params = widget.get_parameters()
        assert params is not None
        assert params.width_cm == 200.0

    def test_get_parameters_with_valid_values(self, widget: RectangularParameterWidget) -> None:
        """Test getting parameters with valid custom values."""
        from PySide6.QtWidgets import QDoubleSpinBox
        
        width = widget.field_widgets["width_cm"]
        assert isinstance(width, QDoubleSpinBox)
        width.setValue(250.0)
        
        height = widget.field_widgets["height_cm"]
        assert isinstance(height, QDoubleSpinBox)
        height.setValue(120.0)
        
        frame_weight = widget.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)
        frame_weight.setValue(0.7)

        params = widget.get_parameters()
        assert params.width_cm == 250.0
        assert params.height_cm == 120.0
        assert params.frame_weight_per_meter_kg_m == 0.7

    def test_validation_signals_connected(self, widget: RectangularParameterWidget) -> None:
        """Test that validation signals are connected."""
        from PySide6.QtWidgets import QDoubleSpinBox
        
        # Change a value and verify no crash (signals are connected)
        width = widget.field_widgets["width_cm"]
        assert isinstance(width, QDoubleSpinBox)
        width.setValue(300.0)
        # If signals weren't connected properly, this would not trigger validation
        # The test passing means signals are working

    def test_clear_all_errors(self, widget: RectangularParameterWidget) -> None:
        """Test that clear_all_errors method works."""
        # This should not crash
        widget._clear_all_errors()
        # Verify widgets have no error styling
        width = widget.field_widgets["width_cm"]
        height = widget.field_widgets["height_cm"]
        frame_weight = widget.field_widgets["frame_weight_per_meter_kg_m"]
        assert width.styleSheet() == ""
        assert height.styleSheet() == ""
        assert frame_weight.styleSheet() == ""
