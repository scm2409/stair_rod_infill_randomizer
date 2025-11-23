"""Parameter widgets for evaluators."""

from abc import ABCMeta, abstractmethod

from pydantic import ValidationError
from PySide6.QtWidgets import QFormLayout, QWidget

from railing_generator.domain.evaluators.evaluator_parameters import EvaluatorParameters


class QWidgetABCMeta(type(QWidget), ABCMeta):  # type: ignore[misc]
    """Metaclass that combines QWidget's metaclass with ABCMeta."""

    pass


class EvaluatorParameterWidget(QWidget, metaclass=QWidgetABCMeta):
    """
    Abstract base class for evaluator parameter input widgets.

    Each evaluator type has a dedicated widget class that:
    - Creates appropriate input controls
    - Loads default values
    - Collects and validates parameters
    - Provides real-time validation feedback

    Subclasses must populate the `field_widgets` dictionary mapping
    Pydantic field names to their corresponding Qt widgets.

    This follows the same pattern as ShapeParameterWidget and GeneratorParameterWidget.
    """

    # Style for invalid input (red border)
    INVALID_STYLE = "border: 2px solid #ff0000;"
    VALID_STYLE = ""

    def __init__(self) -> None:
        """Initialize the parameter widget."""
        super().__init__()
        self.form_layout = QFormLayout(self)

        # Dictionary mapping Pydantic field names to Qt widgets
        # Subclasses populate this in _create_widgets()
        self.field_widgets: dict[str, QWidget] = {}

        self._create_widgets()
        self._load_defaults()
        self._connect_validation_signals()

    @abstractmethod
    def _create_widgets(self) -> None:
        """
        Create input widgets for this evaluator's parameters.

        Must populate self.field_widgets dictionary with mappings from
        Pydantic field names to Qt widgets.
        """
        ...

    @abstractmethod
    def _load_defaults(self) -> None:
        """Load default values into the widgets."""
        ...

    def _connect_validation_signals(self) -> None:
        """
        Connect valueChanged signals to validation for real-time feedback.

        Default implementation does nothing. Subclasses can override if they
        have input widgets that need validation.
        """
        pass

    @abstractmethod
    def get_parameters(self) -> EvaluatorParameters:
        """
        Get the current parameter values as a validated Pydantic model.

        Returns:
            Validated evaluator parameters

        Raises:
            ValidationError: If parameters are invalid
        """
        ...

    def _validate_and_update_ui(self) -> None:
        """
        Validate current parameters and update UI with visual feedback.

        Attempts to create a Pydantic model from current widget values.
        If validation fails, highlights invalid fields with red borders
        and shows error messages in tooltips.
        """
        try:
            # Attempt to get validated parameters
            self.get_parameters()
            # If successful, clear all error styling
            self._clear_all_errors()
        except ValidationError as e:
            # Display validation errors
            self._display_validation_errors(e)

    def _clear_all_errors(self) -> None:
        """Clear error styling from all input widgets."""
        for widget in self.field_widgets.values():
            widget.setStyleSheet(self.VALID_STYLE)
            widget.setToolTip("")

    def _display_validation_errors(self, error: ValidationError) -> None:
        """
        Display validation errors by highlighting invalid fields.

        Args:
            error: Pydantic ValidationError containing field-specific errors
        """
        # First clear all errors
        self._clear_all_errors()

        # Then highlight fields with errors
        for err in error.errors():
            # Get field name from error location
            if err["loc"]:
                field_name = str(err["loc"][0])
                if field_name in self.field_widgets:
                    widget = self.field_widgets[field_name]
                    widget.setStyleSheet(self.INVALID_STYLE)
                    widget.setToolTip(err["msg"])
