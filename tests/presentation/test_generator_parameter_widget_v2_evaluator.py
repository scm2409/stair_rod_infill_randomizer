"""Tests for RandomGeneratorV2ParameterWidget with evaluator integration."""

import pytest

from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
    PassThroughEvaluatorParameters,
)
from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
    RandomGeneratorParametersV2,
)
from railing_generator.presentation.generator_parameter_widget import (
    RandomGeneratorParameterWidgetV2,
)


def test_v2_widget_has_evaluator_selection(qtbot) -> None:  # type: ignore[no-untyped-def]
    """Test that V2 widget includes evaluator selection UI."""
    widget = RandomGeneratorParameterWidgetV2()
    qtbot.addWidget(widget)

    # Should have evaluator type combo box
    assert widget.evaluator_type_combo is not None
    assert widget.evaluator_type_combo.count() > 0

    # Should have evaluator widgets dictionary
    assert len(widget.evaluator_widgets) > 0
    assert "passthrough" in widget.evaluator_widgets


def test_v2_widget_get_parameters_includes_evaluator(qtbot) -> None:  # type: ignore[no-untyped-def]
    """Test that get_parameters includes nested evaluator parameters."""
    widget = RandomGeneratorParameterWidgetV2()
    qtbot.addWidget(widget)

    params = widget.get_parameters()

    assert isinstance(params, RandomGeneratorParametersV2)
    assert hasattr(params, "evaluator")
    assert isinstance(params.evaluator, PassThroughEvaluatorParameters)
    assert params.evaluator.type == "passthrough"


def test_v2_widget_evaluator_type_change(qtbot) -> None:  # type: ignore[no-untyped-def]
    """Test that changing evaluator type shows/hides correct widgets."""
    widget = RandomGeneratorParameterWidgetV2()
    qtbot.addWidget(widget)
    widget.show()  # Show the widget to make children visible

    # Initially, passthrough widget should be visible
    assert widget.evaluator_widgets["passthrough"].isVisible()

    # Change evaluator type (when we add more types, this will be more interesting)
    # For now, just verify the mechanism works
    assert widget.evaluator_type_combo is not None
    widget.evaluator_type_combo.setCurrentText("passthrough")

    # Passthrough widget should still be visible
    assert widget.evaluator_widgets["passthrough"].isVisible()


def test_v2_widget_evaluator_params_serialization(qtbot) -> None:  # type: ignore[no-untyped-def]
    """Test that evaluator parameters can be serialized and deserialized."""
    widget = RandomGeneratorParameterWidgetV2()
    qtbot.addWidget(widget)

    # Get parameters
    params = widget.get_parameters()

    # Serialize to dict
    params_dict = params.model_dump()

    # Should include evaluator with type discriminator
    assert "evaluator" in params_dict
    assert params_dict["evaluator"]["type"] == "passthrough"

    # Deserialize back
    params_restored = RandomGeneratorParametersV2.model_validate(params_dict)

    assert isinstance(params_restored.evaluator, PassThroughEvaluatorParameters)
    assert params_restored.evaluator.type == "passthrough"
