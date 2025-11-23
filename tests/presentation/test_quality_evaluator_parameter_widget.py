"""Tests for Quality Evaluator Parameter Widget."""

import pytest
from pydantic import ValidationError

from railing_generator.domain.evaluators.quality_evaluator_parameters import (
    QualityEvaluatorParameters,
)
from railing_generator.presentation.quality_evaluator_parameter_widget import (
    QualityEvaluatorParameterWidget,
)


class TestQualityEvaluatorParameterWidget:
    """Tests for QualityEvaluatorParameterWidget."""

    def test_widget_creation(self, qtbot) -> None:
        """Test that widget is created successfully."""
        widget = QualityEvaluatorParameterWidget()
        qtbot.addWidget(widget)

        # Should have all field widgets
        assert "max_hole_area_cm2" in widget.field_widgets
        assert "hole_uniformity_weight" in widget.field_widgets
        assert "incircle_uniformity_weight" in widget.field_widgets
        assert "angle_distribution_weight" in widget.field_widgets
        assert "anchor_spacing_horizontal_weight" in widget.field_widgets
        assert "anchor_spacing_vertical_weight" in widget.field_widgets

    def test_default_values_loaded(self, qtbot) -> None:
        """Test that default values are loaded correctly."""
        widget = QualityEvaluatorParameterWidget()
        qtbot.addWidget(widget)

        params = widget.get_parameters()

        # Check that defaults are loaded
        assert params.max_hole_area_cm2 == 10000.0
        assert params.hole_uniformity_weight == 0.3
        assert params.incircle_uniformity_weight == 0.2
        assert params.angle_distribution_weight == 0.2
        assert params.anchor_spacing_horizontal_weight == 0.15
        assert params.anchor_spacing_vertical_weight == 0.15

    def test_get_parameters_returns_valid_model(self, qtbot) -> None:
        """Test that get_parameters returns a valid QualityEvaluatorParameters."""
        widget = QualityEvaluatorParameterWidget()
        qtbot.addWidget(widget)

        params = widget.get_parameters()

        assert isinstance(params, QualityEvaluatorParameters)
        assert params.type == "quality"

    def test_parameter_modification(self, qtbot) -> None:
        """Test that parameter values can be modified."""
        widget = QualityEvaluatorParameterWidget()
        qtbot.addWidget(widget)

        # Modify max hole area
        from PySide6.QtWidgets import QDoubleSpinBox

        max_hole_spin = widget.field_widgets["max_hole_area_cm2"]
        assert isinstance(max_hole_spin, QDoubleSpinBox)
        max_hole_spin.setValue(5000.0)

        # Modify incircle uniformity weight
        incircle_spin = widget.field_widgets["incircle_uniformity_weight"]
        assert isinstance(incircle_spin, QDoubleSpinBox)
        incircle_spin.setValue(0.5)

        params = widget.get_parameters()

        assert params.max_hole_area_cm2 == 5000.0
        assert params.incircle_uniformity_weight == 0.5

    def test_validation_rejects_invalid_max_hole_area(self, qtbot) -> None:
        """Test that validation rejects invalid max hole area."""
        widget = QualityEvaluatorParameterWidget()
        qtbot.addWidget(widget)

        from PySide6.QtWidgets import QDoubleSpinBox

        # Try to set negative value (should be prevented by spinbox range)
        max_hole_spin = widget.field_widgets["max_hole_area_cm2"]
        assert isinstance(max_hole_spin, QDoubleSpinBox)
        max_hole_spin.setValue(-100.0)

        # Spinbox should clamp to minimum (0.1)
        assert max_hole_spin.value() == 0.1

    def test_validation_rejects_invalid_weight(self, qtbot) -> None:
        """Test that validation rejects weights outside [0, 1]."""
        widget = QualityEvaluatorParameterWidget()
        qtbot.addWidget(widget)

        from PySide6.QtWidgets import QDoubleSpinBox

        # Try to set value > 1.0 (should be prevented by spinbox range)
        weight_spin = widget.field_widgets["hole_uniformity_weight"]
        assert isinstance(weight_spin, QDoubleSpinBox)
        weight_spin.setValue(1.5)

        # Spinbox should clamp to maximum (1.0)
        assert weight_spin.value() == 1.0

    def test_weights_can_sum_to_one(self, qtbot) -> None:
        """Test that weights can be configured to sum to 1.0."""
        widget = QualityEvaluatorParameterWidget()
        qtbot.addWidget(widget)

        params = widget.get_parameters()

        # Default weights should sum to approximately 1.0
        total = (
            params.hole_uniformity_weight
            + params.incircle_uniformity_weight
            + params.angle_distribution_weight
            + params.anchor_spacing_horizontal_weight
            + params.anchor_spacing_vertical_weight
        )

        assert abs(total - 1.0) < 0.01
