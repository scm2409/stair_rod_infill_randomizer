"""Base class and implementations for shape parameter widgets."""

from abc import ABCMeta, abstractmethod

from pydantic import ValidationError
from PySide6.QtWidgets import QDoubleSpinBox, QFormLayout, QSpinBox, QWidget

from railing_generator.domain.shapes.parallelogram_railing_shape import (
    ParallelogramRailingShapeDefaults,
    ParallelogramRailingShapeParameters,
)
from railing_generator.domain.shapes.railing_shape_parameters import RailingShapeParameters
from railing_generator.domain.shapes.rectangular_railing_shape import (
    RectangularRailingShapeDefaults,
    RectangularRailingShapeParameters,
)
from railing_generator.domain.shapes.staircase_railing_shape import (
    StaircaseRailingShapeDefaults,
    StaircaseRailingShapeParameters,
)


class QWidgetABCMeta(type(QWidget), ABCMeta):  # type: ignore[misc]
    """Metaclass that combines QWidget's metaclass with ABCMeta."""

    pass


class ShapeParameterWidget(QWidget, metaclass=QWidgetABCMeta):
    """
    Abstract base class for shape parameter input widgets.

    Each shape type has a dedicated widget class that:
    - Creates appropriate input controls
    - Loads default values
    - Collects and validates parameters
    - Provides real-time validation feedback

    Subclasses must populate the `field_widgets` dictionary mapping
    Pydantic field names to their corresponding Qt widgets.
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
        Create input widgets for this shape's parameters.

        Must populate self.field_widgets dictionary with mappings from
        Pydantic field names to Qt widgets.
        """
        ...

    @abstractmethod
    def _load_defaults(self) -> None:
        """Load default values into the widgets."""
        ...

    def _connect_validation_signals(self) -> None:
        """Connect valueChanged signals to validation for real-time feedback."""
        for widget in self.field_widgets.values():
            # Connect appropriate signal based on widget type
            if isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                widget.valueChanged.connect(self._validate_and_update_ui)

    @abstractmethod
    def get_parameters(self) -> RailingShapeParameters:
        """
        Get the current parameter values as a validated Pydantic model.

        Returns:
            Validated shape parameters

        Raises:
            ValidationError: If parameters are invalid
        """
        ...

    @abstractmethod
    def set_parameters(self, params: RailingShapeParameters) -> None:
        """
        Set the widget values from a parameters object.

        Args:
            params: The parameters to load into the widgets
        """
        ...

    def _validate_and_update_ui(self) -> None:
        """
        Validate current parameters and update UI with visual feedback.

        This method attempts to create a Pydantic model with current values.
        If validation fails, it highlights invalid fields with red borders
        and displays error messages as tooltips.
        """
        try:
            # Attempt to get parameters (will raise ValidationError if invalid)
            self.get_parameters()
            # If successful, clear all error styling
            self._clear_all_errors()
        except ValidationError as e:
            # Display errors for each invalid field
            self._display_validation_errors(e)

    def _clear_all_errors(self) -> None:
        """Clear error styling from all input widgets."""
        for widget in self.field_widgets.values():
            self._clear_widget_error(widget)

    def _display_validation_errors(self, error: ValidationError) -> None:
        """
        Display validation errors on the appropriate widgets.

        Args:
            error: The Pydantic ValidationError containing field-specific errors
        """
        # First clear all errors
        self._clear_all_errors()

        # Display error for each invalid field
        for err in error.errors():
            field_name = err["loc"][0] if err["loc"] else None
            if field_name and isinstance(field_name, str) and field_name in self.field_widgets:
                widget = self.field_widgets[field_name]
                error_msg = err["msg"]
                self._set_widget_error(widget, error_msg)

    def _set_widget_error(self, widget: QWidget, error_message: str) -> None:
        """
        Set error styling and tooltip on a widget.

        Args:
            widget: The widget to mark as invalid
            error_message: The error message to display as tooltip
        """
        widget.setStyleSheet(self.INVALID_STYLE)
        widget.setToolTip(error_message)

    def _clear_widget_error(self, widget: QWidget) -> None:
        """
        Clear error styling and tooltip from a widget.

        Args:
            widget: The widget to clear errors from
        """
        widget.setStyleSheet(self.VALID_STYLE)
        widget.setToolTip("")


class StaircaseParameterWidget(ShapeParameterWidget):
    """Parameter widget for staircase-shaped railings."""

    def __init__(self) -> None:
        """Initialize the staircase parameter widget."""
        self._defaults = StaircaseRailingShapeDefaults()
        super().__init__()

    def _create_widgets(self) -> None:
        """Create input widgets for staircase parameters."""
        # Post length
        post_length_spin = QDoubleSpinBox()
        post_length_spin.setRange(1.0, 10000.0)
        post_length_spin.setSuffix(" cm")
        self.form_layout.addRow("Post Length:", post_length_spin)
        self.field_widgets["post_length_cm"] = post_length_spin

        # Stair width
        stair_width_spin = QDoubleSpinBox()
        stair_width_spin.setRange(1.0, 10000.0)
        stair_width_spin.setSuffix(" cm")
        self.form_layout.addRow("Stair Width:", stair_width_spin)
        self.field_widgets["stair_width_cm"] = stair_width_spin

        # Stair height
        stair_height_spin = QDoubleSpinBox()
        stair_height_spin.setRange(1.0, 10000.0)
        stair_height_spin.setSuffix(" cm")
        self.form_layout.addRow("Stair Height:", stair_height_spin)
        self.field_widgets["stair_height_cm"] = stair_height_spin

        # Number of steps
        num_steps_spin = QSpinBox()
        num_steps_spin.setRange(1, 50)
        self.form_layout.addRow("Number of Steps:", num_steps_spin)
        self.field_widgets["num_steps"] = num_steps_spin

        # Frame weight per meter
        frame_weight_spin = QDoubleSpinBox()
        frame_weight_spin.setRange(0.01, 100.0)
        frame_weight_spin.setSuffix(" kg/m")
        frame_weight_spin.setDecimals(2)
        self.form_layout.addRow("Frame Weight:", frame_weight_spin)
        self.field_widgets["frame_weight_per_meter_kg_m"] = frame_weight_spin

    def _load_defaults(self) -> None:
        """Load default values into the widgets."""
        post_length = self.field_widgets["post_length_cm"]
        assert isinstance(post_length, QDoubleSpinBox)
        post_length.setValue(self._defaults.post_length_cm)

        stair_width = self.field_widgets["stair_width_cm"]
        assert isinstance(stair_width, QDoubleSpinBox)
        stair_width.setValue(self._defaults.stair_width_cm)

        stair_height = self.field_widgets["stair_height_cm"]
        assert isinstance(stair_height, QDoubleSpinBox)
        stair_height.setValue(self._defaults.stair_height_cm)

        num_steps = self.field_widgets["num_steps"]
        assert isinstance(num_steps, QSpinBox)
        num_steps.setValue(self._defaults.num_steps)

        frame_weight = self.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)
        frame_weight.setValue(self._defaults.frame_weight_per_meter_kg_m)

    def get_parameters(self) -> StaircaseRailingShapeParameters:
        """
        Get the current staircase parameter values.

        Returns:
            Validated staircase parameters

        Raises:
            ValidationError: If parameters are invalid
        """
        post_length = self.field_widgets["post_length_cm"]
        assert isinstance(post_length, QDoubleSpinBox)

        stair_width = self.field_widgets["stair_width_cm"]
        assert isinstance(stair_width, QDoubleSpinBox)

        stair_height = self.field_widgets["stair_height_cm"]
        assert isinstance(stair_height, QDoubleSpinBox)

        num_steps = self.field_widgets["num_steps"]
        assert isinstance(num_steps, QSpinBox)

        frame_weight = self.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)

        return StaircaseRailingShapeParameters(
            post_length_cm=post_length.value(),
            stair_width_cm=stair_width.value(),
            stair_height_cm=stair_height.value(),
            num_steps=num_steps.value(),
            frame_weight_per_meter_kg_m=frame_weight.value(),
        )

    def set_parameters(self, params: RailingShapeParameters) -> None:
        """Set the widget values from a StaircaseRailingShapeParameters object."""
        if not isinstance(params, StaircaseRailingShapeParameters):
            return

        post_length = self.field_widgets["post_length_cm"]
        assert isinstance(post_length, QDoubleSpinBox)
        post_length.setValue(params.post_length_cm)

        stair_width = self.field_widgets["stair_width_cm"]
        assert isinstance(stair_width, QDoubleSpinBox)
        stair_width.setValue(params.stair_width_cm)

        stair_height = self.field_widgets["stair_height_cm"]
        assert isinstance(stair_height, QDoubleSpinBox)
        stair_height.setValue(params.stair_height_cm)

        num_steps = self.field_widgets["num_steps"]
        assert isinstance(num_steps, QSpinBox)
        num_steps.setValue(params.num_steps)

        frame_weight = self.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)
        frame_weight.setValue(params.frame_weight_per_meter_kg_m)


class RectangularParameterWidget(ShapeParameterWidget):
    """Parameter widget for rectangular-shaped railings."""

    def __init__(self) -> None:
        """Initialize the rectangular parameter widget."""
        self._defaults = RectangularRailingShapeDefaults()
        super().__init__()

    def _create_widgets(self) -> None:
        """Create input widgets for rectangular parameters."""
        # Width
        width_spin = QDoubleSpinBox()
        width_spin.setRange(1.0, 10000.0)
        width_spin.setSuffix(" cm")
        self.form_layout.addRow("Width:", width_spin)
        self.field_widgets["width_cm"] = width_spin

        # Height
        height_spin = QDoubleSpinBox()
        height_spin.setRange(1.0, 10000.0)
        height_spin.setSuffix(" cm")
        self.form_layout.addRow("Height:", height_spin)
        self.field_widgets["height_cm"] = height_spin

        # Frame weight per meter
        frame_weight_spin = QDoubleSpinBox()
        frame_weight_spin.setRange(0.01, 100.0)
        frame_weight_spin.setSuffix(" kg/m")
        frame_weight_spin.setDecimals(2)
        self.form_layout.addRow("Frame Weight:", frame_weight_spin)
        self.field_widgets["frame_weight_per_meter_kg_m"] = frame_weight_spin

    def _load_defaults(self) -> None:
        """Load default values into the widgets."""
        width = self.field_widgets["width_cm"]
        assert isinstance(width, QDoubleSpinBox)
        width.setValue(self._defaults.width_cm)

        height = self.field_widgets["height_cm"]
        assert isinstance(height, QDoubleSpinBox)
        height.setValue(self._defaults.height_cm)

        frame_weight = self.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)
        frame_weight.setValue(self._defaults.frame_weight_per_meter_kg_m)

    def get_parameters(self) -> RectangularRailingShapeParameters:
        """
        Get the current rectangular parameter values.

        Returns:
            Validated rectangular parameters

        Raises:
            ValidationError: If parameters are invalid
        """
        width = self.field_widgets["width_cm"]
        assert isinstance(width, QDoubleSpinBox)

        height = self.field_widgets["height_cm"]
        assert isinstance(height, QDoubleSpinBox)

        frame_weight = self.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)

        return RectangularRailingShapeParameters(
            width_cm=width.value(),
            height_cm=height.value(),
            frame_weight_per_meter_kg_m=frame_weight.value(),
        )

    def set_parameters(self, params: RailingShapeParameters) -> None:
        """Set the widget values from a RectangularRailingShapeParameters object."""
        if not isinstance(params, RectangularRailingShapeParameters):
            return

        width = self.field_widgets["width_cm"]
        assert isinstance(width, QDoubleSpinBox)
        width.setValue(params.width_cm)

        height = self.field_widgets["height_cm"]
        assert isinstance(height, QDoubleSpinBox)
        height.setValue(params.height_cm)

        frame_weight = self.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)
        frame_weight.setValue(params.frame_weight_per_meter_kg_m)


class ParallelogramParameterWidget(ShapeParameterWidget):
    """Parameter widget for parallelogram-shaped railings."""

    def __init__(self) -> None:
        """Initialize the parallelogram parameter widget."""
        self._defaults = ParallelogramRailingShapeDefaults()
        super().__init__()

    def _create_widgets(self) -> None:
        """Create input widgets for parallelogram parameters."""
        # Post length
        post_length_spin = QDoubleSpinBox()
        post_length_spin.setRange(1.0, 10000.0)
        post_length_spin.setSuffix(" cm")
        self.form_layout.addRow("Post Length:", post_length_spin)
        self.field_widgets["post_length_cm"] = post_length_spin

        # Slope width
        slope_width_spin = QDoubleSpinBox()
        slope_width_spin.setRange(1.0, 10000.0)
        slope_width_spin.setSuffix(" cm")
        self.form_layout.addRow("Slope Width:", slope_width_spin)
        self.field_widgets["slope_width_cm"] = slope_width_spin

        # Slope height
        slope_height_spin = QDoubleSpinBox()
        slope_height_spin.setRange(1.0, 10000.0)
        slope_height_spin.setSuffix(" cm")
        self.form_layout.addRow("Slope Height:", slope_height_spin)
        self.field_widgets["slope_height_cm"] = slope_height_spin

        # Frame weight per meter
        frame_weight_spin = QDoubleSpinBox()
        frame_weight_spin.setRange(0.01, 100.0)
        frame_weight_spin.setSuffix(" kg/m")
        frame_weight_spin.setDecimals(2)
        self.form_layout.addRow("Frame Weight:", frame_weight_spin)
        self.field_widgets["frame_weight_per_meter_kg_m"] = frame_weight_spin

    def _load_defaults(self) -> None:
        """Load default values into the widgets."""
        post_length = self.field_widgets["post_length_cm"]
        assert isinstance(post_length, QDoubleSpinBox)
        post_length.setValue(self._defaults.post_length_cm)

        slope_width = self.field_widgets["slope_width_cm"]
        assert isinstance(slope_width, QDoubleSpinBox)
        slope_width.setValue(self._defaults.slope_width_cm)

        slope_height = self.field_widgets["slope_height_cm"]
        assert isinstance(slope_height, QDoubleSpinBox)
        slope_height.setValue(self._defaults.slope_height_cm)

        frame_weight = self.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)
        frame_weight.setValue(self._defaults.frame_weight_per_meter_kg_m)

    def get_parameters(self) -> ParallelogramRailingShapeParameters:
        """
        Get the current parallelogram parameter values.

        Returns:
            Validated parallelogram parameters

        Raises:
            ValidationError: If parameters are invalid
        """
        post_length = self.field_widgets["post_length_cm"]
        assert isinstance(post_length, QDoubleSpinBox)

        slope_width = self.field_widgets["slope_width_cm"]
        assert isinstance(slope_width, QDoubleSpinBox)

        slope_height = self.field_widgets["slope_height_cm"]
        assert isinstance(slope_height, QDoubleSpinBox)

        frame_weight = self.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)

        return ParallelogramRailingShapeParameters(
            post_length_cm=post_length.value(),
            slope_width_cm=slope_width.value(),
            slope_height_cm=slope_height.value(),
            frame_weight_per_meter_kg_m=frame_weight.value(),
        )

    def set_parameters(self, params: RailingShapeParameters) -> None:
        """Set the widget values from a ParallelogramRailingShapeParameters object."""
        if not isinstance(params, ParallelogramRailingShapeParameters):
            return

        post_length = self.field_widgets["post_length_cm"]
        assert isinstance(post_length, QDoubleSpinBox)
        post_length.setValue(params.post_length_cm)

        slope_width = self.field_widgets["slope_width_cm"]
        assert isinstance(slope_width, QDoubleSpinBox)
        slope_width.setValue(params.slope_width_cm)

        slope_height = self.field_widgets["slope_height_cm"]
        assert isinstance(slope_height, QDoubleSpinBox)
        slope_height.setValue(params.slope_height_cm)

        frame_weight = self.field_widgets["frame_weight_per_meter_kg_m"]
        assert isinstance(frame_weight, QDoubleSpinBox)
        frame_weight.setValue(params.frame_weight_per_meter_kg_m)
