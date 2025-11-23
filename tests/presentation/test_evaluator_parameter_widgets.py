"""Tests for evaluator parameter widgets."""

import pytest

from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
    PassThroughEvaluatorParameters,
)
from railing_generator.presentation.passthrough_evaluator_parameter_widget import (
    PassThroughEvaluatorParameterWidget,
)


def test_passthrough_evaluator_widget_initialization(qtbot) -> None:  # type: ignore[no-untyped-def]
    """Test PassThroughEvaluatorParameterWidget initialization."""
    widget = PassThroughEvaluatorParameterWidget()
    qtbot.addWidget(widget)

    assert widget is not None
    assert widget.form_layout is not None


def test_passthrough_evaluator_widget_get_parameters(qtbot) -> None:  # type: ignore[no-untyped-def]
    """Test getting parameters from PassThroughEvaluatorParameterWidget."""
    widget = PassThroughEvaluatorParameterWidget()
    qtbot.addWidget(widget)

    params = widget.get_parameters()

    assert isinstance(params, PassThroughEvaluatorParameters)
    assert params.type == "passthrough"


def test_passthrough_evaluator_widget_has_info_label(qtbot) -> None:  # type: ignore[no-untyped-def]
    """Test that PassThroughEvaluatorParameterWidget displays informational text."""
    widget = PassThroughEvaluatorParameterWidget()
    qtbot.addWidget(widget)

    # Widget should have a label with information
    assert widget.form_layout.rowCount() > 0
