"""Parameter widget for Pass-Through Evaluator."""

from PySide6.QtWidgets import QLabel

from railing_generator.domain.evaluators.evaluator_parameters import EvaluatorParameters
from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
    PassThroughEvaluatorParameters,
)
from railing_generator.presentation.evaluator_parameter_widget import EvaluatorParameterWidget


class PassThroughEvaluatorParameterWidget(EvaluatorParameterWidget):
    """
    Parameter widget for Pass-Through Evaluator.

    The Pass-Through Evaluator has no configurable parameters,
    so this widget just displays an informational message.
    """

    def _create_widgets(self) -> None:
        """Create informational label (no input widgets needed)."""
        info_label = QLabel(
            "Pass-Through Evaluator has no parameters.\n"
            "It accepts all arrangements without scoring (fastest option)."
        )
        info_label.setWordWrap(True)
        self.form_layout.addRow(info_label)

    def _load_defaults(self) -> None:
        """No defaults to load (no parameters)."""
        pass

    def get_parameters(self) -> PassThroughEvaluatorParameters:
        """
        Get Pass-Through Evaluator parameters.

        Returns:
            PassThroughEvaluatorParameters with default values
        """
        return PassThroughEvaluatorParameters()

    def set_parameters(
        self, params: "EvaluatorParameters | PassThroughEvaluatorParameters"
    ) -> None:
        """Set parameters (no-op for Pass-Through Evaluator)."""
        # Pass-Through Evaluator has no configurable parameters
        pass
