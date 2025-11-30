"""Parameter widgets for infill generators."""

from abc import ABCMeta, abstractmethod

from pydantic import ValidationError
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorParameters,
)
from railing_generator.domain.infill_generators.random_generator_parameters import (
    RandomGeneratorDefaults,
    RandomGeneratorParameters,
)
from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
    RandomGeneratorDefaultsV2,
    RandomGeneratorParametersV2,
)
from railing_generator.presentation.evaluator_parameter_widget import EvaluatorParameterWidget
from railing_generator.presentation.passthrough_evaluator_parameter_widget import (
    PassThroughEvaluatorParameterWidget,
)
from railing_generator.presentation.quality_evaluator_parameter_widget import (
    QualityEvaluatorParameterWidget,
)


class QWidgetABCMeta(type(QWidget), ABCMeta):  # type: ignore[misc]
    """Metaclass that combines QWidget's metaclass with ABCMeta."""

    pass


class GeneratorParameterWidget(QWidget, metaclass=QWidgetABCMeta):
    """
    Abstract base class for generator parameter input widgets.

    Each generator type has a dedicated widget class that:
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
        Create input widgets for this generator's parameters.

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
    def get_parameters(self) -> InfillGeneratorParameters:
        """
        Get the current parameter values as a validated Pydantic model.

        Returns:
            Validated generator parameters

        Raises:
            ValidationError: If parameters are invalid
        """
        ...

    @abstractmethod
    def set_parameters(self, params: InfillGeneratorParameters) -> None:
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


class RandomGeneratorParameterWidget(GeneratorParameterWidget):
    """
    Parameter widget for random generator configuration.

    Provides input fields for all random generator parameters with validation.
    """

    def __init__(self) -> None:
        """Initialize the random generator parameter widget."""
        self._defaults = RandomGeneratorDefaults()
        super().__init__()

    def _create_widgets(self) -> None:
        """Create input widgets for random generator parameters."""

        # Number of rods
        num_rods_spin = QSpinBox()
        num_rods_spin.setRange(1, 200)
        num_rods_spin.setSuffix(" rods")
        self.form_layout.addRow("Number of Rods:", num_rods_spin)
        self.field_widgets["num_rods"] = num_rods_spin

        # Min rod length
        min_rod_length_spin = QDoubleSpinBox()
        min_rod_length_spin.setRange(1.0, 1000.0)
        min_rod_length_spin.setSuffix(" cm")
        min_rod_length_spin.setDecimals(1)
        self.form_layout.addRow("Min Rod Length:", min_rod_length_spin)
        self.field_widgets["min_rod_length_cm"] = min_rod_length_spin

        # Max rod length
        max_rod_length_spin = QDoubleSpinBox()
        max_rod_length_spin.setRange(1.0, 1000.0)
        max_rod_length_spin.setSuffix(" cm")
        max_rod_length_spin.setDecimals(1)
        self.form_layout.addRow("Max Rod Length:", max_rod_length_spin)
        self.field_widgets["max_rod_length_cm"] = max_rod_length_spin

        # Max angle deviation
        max_angle_spin = QDoubleSpinBox()
        max_angle_spin.setRange(0.0, 75.0)
        max_angle_spin.setSuffix(" °")
        max_angle_spin.setDecimals(1)
        self.form_layout.addRow("Max Angle Deviation:", max_angle_spin)
        self.field_widgets["max_angle_deviation_deg"] = max_angle_spin

        # Number of layers
        num_layers_spin = QSpinBox()
        num_layers_spin.setRange(1, 5)
        num_layers_spin.setSuffix(" layers")
        self.form_layout.addRow("Number of Layers:", num_layers_spin)
        self.field_widgets["num_layers"] = num_layers_spin

        # Min anchor distance
        min_anchor_distance_spin = QDoubleSpinBox()
        min_anchor_distance_spin.setRange(0.1, 100.0)
        min_anchor_distance_spin.setSuffix(" cm")
        min_anchor_distance_spin.setDecimals(1)
        self.form_layout.addRow("Min Anchor Distance:", min_anchor_distance_spin)
        self.field_widgets["min_anchor_distance_cm"] = min_anchor_distance_spin

        # Max iterations
        max_iterations_spin = QSpinBox()
        max_iterations_spin.setRange(1, 1000000)
        self.form_layout.addRow("Max Iterations:", max_iterations_spin)
        self.field_widgets["max_iterations"] = max_iterations_spin

        # Max duration
        max_duration_spin = QDoubleSpinBox()
        max_duration_spin.setRange(1, 3600.0)
        max_duration_spin.setSuffix(" sec")
        max_duration_spin.setDecimals(0)
        self.form_layout.addRow("Max Duration:", max_duration_spin)
        self.field_widgets["max_duration_sec"] = max_duration_spin

        # Infill weight per meter
        infill_weight_spin = QDoubleSpinBox()
        infill_weight_spin.setRange(0.01, 10.0)
        infill_weight_spin.setSuffix(" kg/m")
        infill_weight_spin.setDecimals(2)
        self.form_layout.addRow("Infill Weight/Meter:", infill_weight_spin)
        self.field_widgets["infill_weight_per_meter_kg_m"] = infill_weight_spin

    def _load_defaults(self) -> None:
        """Load default values into the widgets."""
        num_rods = self.field_widgets["num_rods"]
        assert isinstance(num_rods, QSpinBox)
        num_rods.setValue(self._defaults.num_rods)

        min_rod_length = self.field_widgets["min_rod_length_cm"]
        assert isinstance(min_rod_length, QDoubleSpinBox)
        min_rod_length.setValue(self._defaults.min_rod_length_cm)

        max_rod_length = self.field_widgets["max_rod_length_cm"]
        assert isinstance(max_rod_length, QDoubleSpinBox)
        max_rod_length.setValue(self._defaults.max_rod_length_cm)

        max_angle = self.field_widgets["max_angle_deviation_deg"]
        assert isinstance(max_angle, QDoubleSpinBox)
        max_angle.setValue(self._defaults.max_angle_deviation_deg)

        num_layers = self.field_widgets["num_layers"]
        assert isinstance(num_layers, QSpinBox)
        num_layers.setValue(self._defaults.num_layers)

        min_anchor_distance = self.field_widgets["min_anchor_distance_cm"]
        assert isinstance(min_anchor_distance, QDoubleSpinBox)
        min_anchor_distance.setValue(self._defaults.min_anchor_distance_cm)

        max_iterations = self.field_widgets["max_iterations"]
        assert isinstance(max_iterations, QSpinBox)
        max_iterations.setValue(self._defaults.max_iterations)

        max_duration = self.field_widgets["max_duration_sec"]
        assert isinstance(max_duration, QDoubleSpinBox)
        max_duration.setValue(self._defaults.max_duration_sec)

        infill_weight = self.field_widgets["infill_weight_per_meter_kg_m"]
        assert isinstance(infill_weight, QDoubleSpinBox)
        infill_weight.setValue(self._defaults.infill_weight_per_meter_kg_m)

    def get_parameters(self) -> RandomGeneratorParameters:
        """
        Get the current parameter values as a RandomGeneratorParameters instance.

        Returns:
            RandomGeneratorParameters with current widget values
        """
        num_rods = self.field_widgets["num_rods"]
        assert isinstance(num_rods, QSpinBox)

        min_rod_length = self.field_widgets["min_rod_length_cm"]
        assert isinstance(min_rod_length, QDoubleSpinBox)

        max_rod_length = self.field_widgets["max_rod_length_cm"]
        assert isinstance(max_rod_length, QDoubleSpinBox)

        max_angle = self.field_widgets["max_angle_deviation_deg"]
        assert isinstance(max_angle, QDoubleSpinBox)

        num_layers = self.field_widgets["num_layers"]
        assert isinstance(num_layers, QSpinBox)

        min_anchor_distance = self.field_widgets["min_anchor_distance_cm"]
        assert isinstance(min_anchor_distance, QDoubleSpinBox)

        max_iterations = self.field_widgets["max_iterations"]
        assert isinstance(max_iterations, QSpinBox)

        max_duration = self.field_widgets["max_duration_sec"]
        assert isinstance(max_duration, QDoubleSpinBox)

        infill_weight = self.field_widgets["infill_weight_per_meter_kg_m"]
        assert isinstance(infill_weight, QDoubleSpinBox)

        return RandomGeneratorParameters(
            num_rods=num_rods.value(),
            min_rod_length_cm=min_rod_length.value(),
            max_rod_length_cm=max_rod_length.value(),
            max_angle_deviation_deg=max_angle.value(),
            num_layers=num_layers.value(),
            min_anchor_distance_cm=min_anchor_distance.value(),
            max_iterations=max_iterations.value(),
            max_duration_sec=max_duration.value(),
            infill_weight_per_meter_kg_m=infill_weight.value(),
        )

    def set_parameters(self, params: InfillGeneratorParameters) -> None:
        """Set the widget values from a RandomGeneratorParameters object."""
        if not isinstance(params, RandomGeneratorParameters):
            return

        num_rods = self.field_widgets["num_rods"]
        assert isinstance(num_rods, QSpinBox)
        num_rods.setValue(params.num_rods)

        min_rod_length = self.field_widgets["min_rod_length_cm"]
        assert isinstance(min_rod_length, QDoubleSpinBox)
        min_rod_length.setValue(params.min_rod_length_cm)

        max_rod_length = self.field_widgets["max_rod_length_cm"]
        assert isinstance(max_rod_length, QDoubleSpinBox)
        max_rod_length.setValue(params.max_rod_length_cm)

        max_angle = self.field_widgets["max_angle_deviation_deg"]
        assert isinstance(max_angle, QDoubleSpinBox)
        max_angle.setValue(params.max_angle_deviation_deg)

        num_layers = self.field_widgets["num_layers"]
        assert isinstance(num_layers, QSpinBox)
        num_layers.setValue(params.num_layers)

        min_anchor_distance = self.field_widgets["min_anchor_distance_cm"]
        assert isinstance(min_anchor_distance, QDoubleSpinBox)
        min_anchor_distance.setValue(params.min_anchor_distance_cm)

        max_iterations = self.field_widgets["max_iterations"]
        assert isinstance(max_iterations, QSpinBox)
        max_iterations.setValue(params.max_iterations)

        max_duration = self.field_widgets["max_duration_sec"]
        assert isinstance(max_duration, QDoubleSpinBox)
        max_duration.setValue(params.max_duration_sec)

        infill_weight = self.field_widgets["infill_weight_per_meter_kg_m"]
        assert isinstance(infill_weight, QDoubleSpinBox)
        infill_weight.setValue(params.infill_weight_per_meter_kg_m)


class RandomGeneratorParameterWidgetV2(GeneratorParameterWidget):
    """
    Parameter widget for random generator v2 configuration.

    Provides input fields for all random generator v2 parameters with validation,
    including nested evaluator parameter selection.
    """

    def __init__(self) -> None:
        """Initialize the random generator v2 parameter widget."""
        self._defaults = RandomGeneratorDefaultsV2()
        # Dictionary of evaluator widgets (created in _create_widgets)
        self.evaluator_widgets: dict[str, EvaluatorParameterWidget] = {}
        self.evaluator_type_combo: QComboBox | None = None
        self.evaluator_container: QWidget | None = None
        super().__init__()

    def _create_widgets(self) -> None:
        """Create input widgets for random generator v2 parameters."""
        # Number of rods
        num_rods_spin = QSpinBox()
        num_rods_spin.setRange(1, 200)
        num_rods_spin.setSuffix(" rods")
        self.form_layout.addRow("Number of Rods:", num_rods_spin)
        self.field_widgets["num_rods"] = num_rods_spin

        # Min rod length
        min_rod_length_spin = QDoubleSpinBox()
        min_rod_length_spin.setRange(1.0, 1000.0)
        min_rod_length_spin.setSuffix(" cm")
        min_rod_length_spin.setDecimals(1)
        self.form_layout.addRow("Min Rod Length:", min_rod_length_spin)
        self.field_widgets["min_rod_length_cm"] = min_rod_length_spin

        # Max rod length
        max_rod_length_spin = QDoubleSpinBox()
        max_rod_length_spin.setRange(1.0, 1000.0)
        max_rod_length_spin.setSuffix(" cm")
        max_rod_length_spin.setDecimals(1)
        self.form_layout.addRow("Max Rod Length:", max_rod_length_spin)
        self.field_widgets["max_rod_length_cm"] = max_rod_length_spin

        # Max angle deviation
        max_angle_spin = QDoubleSpinBox()
        max_angle_spin.setRange(0.0, 75.0)
        max_angle_spin.setSuffix(" °")
        max_angle_spin.setDecimals(1)
        self.form_layout.addRow("Max Angle Deviation:", max_angle_spin)
        self.field_widgets["max_angle_deviation_deg"] = max_angle_spin

        # Number of layers
        num_layers_spin = QSpinBox()
        num_layers_spin.setRange(1, 5)
        num_layers_spin.setSuffix(" layers")
        self.form_layout.addRow("Number of Layers:", num_layers_spin)
        self.field_widgets["num_layers"] = num_layers_spin

        # Min anchor distance (vertical)
        min_anchor_distance_vertical_spin = QDoubleSpinBox()
        min_anchor_distance_vertical_spin.setRange(0.1, 100.0)
        min_anchor_distance_vertical_spin.setSuffix(" cm")
        min_anchor_distance_vertical_spin.setDecimals(1)
        self.form_layout.addRow(
            "Min Anchor Distance (Vertical):", min_anchor_distance_vertical_spin
        )
        self.field_widgets["min_anchor_distance_vertical_cm"] = min_anchor_distance_vertical_spin

        # Min anchor distance (other)
        min_anchor_distance_other_spin = QDoubleSpinBox()
        min_anchor_distance_other_spin.setRange(0.1, 100.0)
        min_anchor_distance_other_spin.setSuffix(" cm")
        min_anchor_distance_other_spin.setDecimals(1)
        self.form_layout.addRow("Min Anchor Distance (Other):", min_anchor_distance_other_spin)
        self.field_widgets["min_anchor_distance_other_cm"] = min_anchor_distance_other_spin

        # Main direction range min
        main_direction_min_spin = QDoubleSpinBox()
        main_direction_min_spin.setRange(-90.0, 90.0)
        main_direction_min_spin.setSuffix(" °")
        main_direction_min_spin.setDecimals(1)
        self.form_layout.addRow("Main Direction Min:", main_direction_min_spin)
        self.field_widgets["main_direction_range_min_deg"] = main_direction_min_spin

        # Main direction range max
        main_direction_max_spin = QDoubleSpinBox()
        main_direction_max_spin.setRange(-90.0, 90.0)
        main_direction_max_spin.setSuffix(" °")
        main_direction_max_spin.setDecimals(1)
        self.form_layout.addRow("Main Direction Max:", main_direction_max_spin)
        self.field_widgets["main_direction_range_max_deg"] = main_direction_max_spin

        # Random angle deviation
        random_angle_deviation_spin = QDoubleSpinBox()
        random_angle_deviation_spin.setRange(0.0, 90.0)
        random_angle_deviation_spin.setSuffix(" °")
        random_angle_deviation_spin.setDecimals(1)
        self.form_layout.addRow("Random Angle Deviation:", random_angle_deviation_spin)
        self.field_widgets["random_angle_deviation_deg"] = random_angle_deviation_spin

        # Max iterations
        max_iterations_spin = QSpinBox()
        max_iterations_spin.setRange(1, 1000000)
        self.form_layout.addRow("Max Iterations:", max_iterations_spin)
        self.field_widgets["max_iterations"] = max_iterations_spin

        # Max duration
        max_duration_spin = QDoubleSpinBox()
        max_duration_spin.setRange(1, 3600.0)
        max_duration_spin.setSuffix(" sec")
        max_duration_spin.setDecimals(0)
        self.form_layout.addRow("Max Duration:", max_duration_spin)
        self.field_widgets["max_duration_sec"] = max_duration_spin

        # Evaluation loop parameters
        self.form_layout.addRow(QLabel())  # Spacer
        evaluation_label = QLabel("<b>Evaluation Loop (Outer Loop)</b>")
        self.form_layout.addRow(evaluation_label)

        # Max evaluation attempts
        max_eval_attempts_spin = QSpinBox()
        max_eval_attempts_spin.setRange(1, 10000000)
        self.form_layout.addRow("Max Evaluation Attempts:", max_eval_attempts_spin)
        self.field_widgets["max_evaluation_attempts"] = max_eval_attempts_spin

        # Max evaluation duration
        max_eval_duration_spin = QDoubleSpinBox()
        max_eval_duration_spin.setRange(1, 60000.0)
        max_eval_duration_spin.setSuffix(" sec")
        max_eval_duration_spin.setDecimals(0)
        self.form_layout.addRow("Max Evaluation Duration:", max_eval_duration_spin)
        self.field_widgets["max_evaluation_duration_sec"] = max_eval_duration_spin

        # Min acceptable fitness
        min_fitness_spin = QDoubleSpinBox()
        min_fitness_spin.setRange(0.0, 1.0)
        min_fitness_spin.setDecimals(2)
        min_fitness_spin.setSingleStep(0.05)
        self.form_layout.addRow("Min Acceptable Fitness:", min_fitness_spin)
        self.field_widgets["min_acceptable_fitness"] = min_fitness_spin

        # Infill weight per meter
        self.form_layout.addRow(QLabel())  # Spacer
        infill_weight_spin = QDoubleSpinBox()
        infill_weight_spin.setRange(0.01, 10.0)
        infill_weight_spin.setSuffix(" kg/m")
        infill_weight_spin.setDecimals(2)
        self.form_layout.addRow("Infill Weight/Meter:", infill_weight_spin)
        self.field_widgets["infill_weight_per_meter_kg_m"] = infill_weight_spin

        # Evaluator selection section
        self.form_layout.addRow(QLabel())  # Spacer
        evaluator_label = QLabel("<b>Evaluator Configuration</b>")
        self.form_layout.addRow(evaluator_label)

        # Evaluator type dropdown
        self.evaluator_type_combo = QComboBox()
        self.evaluator_type_combo.addItems(["passthrough", "quality"])
        self.form_layout.addRow("Evaluator Type:", self.evaluator_type_combo)

        # Container for evaluator parameter widgets
        self.evaluator_container = QWidget()
        evaluator_container_layout = QVBoxLayout(self.evaluator_container)
        evaluator_container_layout.setContentsMargins(0, 0, 0, 0)

        # Create evaluator widgets
        self.evaluator_widgets["passthrough"] = PassThroughEvaluatorParameterWidget()
        self.evaluator_widgets["quality"] = QualityEvaluatorParameterWidget()

        # Add all evaluator widgets to container (hide all except first)
        for widget in self.evaluator_widgets.values():
            evaluator_container_layout.addWidget(widget)
            widget.hide()

        # Show the default evaluator widget
        self.evaluator_widgets["passthrough"].show()

        # Add container to form
        self.form_layout.addRow(self.evaluator_container)

        # Connect evaluator type change signal
        self.evaluator_type_combo.currentTextChanged.connect(self._on_evaluator_type_changed)

    def _on_evaluator_type_changed(self, evaluator_type: str) -> None:
        """Handle evaluator type selection change."""
        # Hide all evaluator widgets
        for widget in self.evaluator_widgets.values():
            widget.hide()

        # Show the selected evaluator widget
        if evaluator_type in self.evaluator_widgets:
            self.evaluator_widgets[evaluator_type].show()

    def _load_defaults(self) -> None:
        """Load default values into the widgets."""
        num_rods = self.field_widgets["num_rods"]
        assert isinstance(num_rods, QSpinBox)
        num_rods.setValue(self._defaults.num_rods)

        min_rod_length = self.field_widgets["min_rod_length_cm"]
        assert isinstance(min_rod_length, QDoubleSpinBox)
        min_rod_length.setValue(self._defaults.min_rod_length_cm)

        max_rod_length = self.field_widgets["max_rod_length_cm"]
        assert isinstance(max_rod_length, QDoubleSpinBox)
        max_rod_length.setValue(self._defaults.max_rod_length_cm)

        max_angle = self.field_widgets["max_angle_deviation_deg"]
        assert isinstance(max_angle, QDoubleSpinBox)
        max_angle.setValue(self._defaults.max_angle_deviation_deg)

        num_layers = self.field_widgets["num_layers"]
        assert isinstance(num_layers, QSpinBox)
        num_layers.setValue(self._defaults.num_layers)

        min_anchor_distance_vertical = self.field_widgets["min_anchor_distance_vertical_cm"]
        assert isinstance(min_anchor_distance_vertical, QDoubleSpinBox)
        min_anchor_distance_vertical.setValue(self._defaults.min_anchor_distance_vertical_cm)

        min_anchor_distance_other = self.field_widgets["min_anchor_distance_other_cm"]
        assert isinstance(min_anchor_distance_other, QDoubleSpinBox)
        min_anchor_distance_other.setValue(self._defaults.min_anchor_distance_other_cm)

        main_direction_min = self.field_widgets["main_direction_range_min_deg"]
        assert isinstance(main_direction_min, QDoubleSpinBox)
        main_direction_min.setValue(self._defaults.main_direction_range_min_deg)

        main_direction_max = self.field_widgets["main_direction_range_max_deg"]
        assert isinstance(main_direction_max, QDoubleSpinBox)
        main_direction_max.setValue(self._defaults.main_direction_range_max_deg)

        random_angle_deviation = self.field_widgets["random_angle_deviation_deg"]
        assert isinstance(random_angle_deviation, QDoubleSpinBox)
        random_angle_deviation.setValue(self._defaults.random_angle_deviation_deg)

        max_iterations = self.field_widgets["max_iterations"]
        assert isinstance(max_iterations, QSpinBox)
        max_iterations.setValue(self._defaults.max_iterations)

        max_duration = self.field_widgets["max_duration_sec"]
        assert isinstance(max_duration, QDoubleSpinBox)
        max_duration.setValue(self._defaults.max_duration_sec)

        max_eval_attempts = self.field_widgets["max_evaluation_attempts"]
        assert isinstance(max_eval_attempts, QSpinBox)
        max_eval_attempts.setValue(self._defaults.max_evaluation_attempts)

        max_eval_duration = self.field_widgets["max_evaluation_duration_sec"]
        assert isinstance(max_eval_duration, QDoubleSpinBox)
        max_eval_duration.setValue(self._defaults.max_evaluation_duration_sec)

        min_fitness = self.field_widgets["min_acceptable_fitness"]
        assert isinstance(min_fitness, QDoubleSpinBox)
        min_fitness.setValue(self._defaults.min_acceptable_fitness)

        infill_weight = self.field_widgets["infill_weight_per_meter_kg_m"]
        assert isinstance(infill_weight, QDoubleSpinBox)
        infill_weight.setValue(self._defaults.infill_weight_per_meter_kg_m)

    def get_parameters(self) -> RandomGeneratorParametersV2:
        """
        Get the current parameter values as a RandomGeneratorParametersV2 instance.

        Returns:
            RandomGeneratorParametersV2 with current widget values
        """
        num_rods = self.field_widgets["num_rods"]
        assert isinstance(num_rods, QSpinBox)

        min_rod_length = self.field_widgets["min_rod_length_cm"]
        assert isinstance(min_rod_length, QDoubleSpinBox)

        max_rod_length = self.field_widgets["max_rod_length_cm"]
        assert isinstance(max_rod_length, QDoubleSpinBox)

        max_angle = self.field_widgets["max_angle_deviation_deg"]
        assert isinstance(max_angle, QDoubleSpinBox)

        num_layers = self.field_widgets["num_layers"]
        assert isinstance(num_layers, QSpinBox)

        min_anchor_distance_vertical = self.field_widgets["min_anchor_distance_vertical_cm"]
        assert isinstance(min_anchor_distance_vertical, QDoubleSpinBox)

        min_anchor_distance_other = self.field_widgets["min_anchor_distance_other_cm"]
        assert isinstance(min_anchor_distance_other, QDoubleSpinBox)

        main_direction_min = self.field_widgets["main_direction_range_min_deg"]
        assert isinstance(main_direction_min, QDoubleSpinBox)

        main_direction_max = self.field_widgets["main_direction_range_max_deg"]
        assert isinstance(main_direction_max, QDoubleSpinBox)

        random_angle_deviation = self.field_widgets["random_angle_deviation_deg"]
        assert isinstance(random_angle_deviation, QDoubleSpinBox)

        max_iterations = self.field_widgets["max_iterations"]
        assert isinstance(max_iterations, QSpinBox)

        max_duration = self.field_widgets["max_duration_sec"]
        assert isinstance(max_duration, QDoubleSpinBox)

        infill_weight = self.field_widgets["infill_weight_per_meter_kg_m"]
        assert isinstance(infill_weight, QDoubleSpinBox)

        # Get evaluator parameters from the active evaluator widget
        assert self.evaluator_type_combo is not None
        evaluator_type = self.evaluator_type_combo.currentText()
        evaluator_params = self.evaluator_widgets[evaluator_type].get_parameters()

        # Type narrowing: evaluator_params is EvaluatorParameters, which is compatible
        # with the union type expected by RandomGeneratorParametersV2
        from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
            EvaluatorParametersUnion,
        )
        from typing import cast

        evaluator_params_typed = cast(EvaluatorParametersUnion, evaluator_params)

        # Get evaluation loop parameters
        max_eval_attempts = self.field_widgets["max_evaluation_attempts"]
        assert isinstance(max_eval_attempts, QSpinBox)

        max_eval_duration = self.field_widgets["max_evaluation_duration_sec"]
        assert isinstance(max_eval_duration, QDoubleSpinBox)

        min_fitness = self.field_widgets["min_acceptable_fitness"]
        assert isinstance(min_fitness, QDoubleSpinBox)

        return RandomGeneratorParametersV2(
            num_rods=num_rods.value(),
            min_rod_length_cm=min_rod_length.value(),
            max_rod_length_cm=max_rod_length.value(),
            max_angle_deviation_deg=max_angle.value(),
            num_layers=num_layers.value(),
            min_anchor_distance_vertical_cm=min_anchor_distance_vertical.value(),
            min_anchor_distance_other_cm=min_anchor_distance_other.value(),
            main_direction_range_min_deg=main_direction_min.value(),
            main_direction_range_max_deg=main_direction_max.value(),
            random_angle_deviation_deg=random_angle_deviation.value(),
            max_iterations=max_iterations.value(),
            max_duration_sec=max_duration.value(),
            max_evaluation_attempts=max_eval_attempts.value(),
            max_evaluation_duration_sec=max_eval_duration.value(),
            min_acceptable_fitness=min_fitness.value(),
            infill_weight_per_meter_kg_m=infill_weight.value(),
            evaluator=evaluator_params_typed,  # Nested evaluator parameters
        )

    def set_parameters(self, params: InfillGeneratorParameters) -> None:
        """Set the widget values from a RandomGeneratorParametersV2 object."""
        if not isinstance(params, RandomGeneratorParametersV2):
            return

        num_rods = self.field_widgets["num_rods"]
        assert isinstance(num_rods, QSpinBox)
        num_rods.setValue(params.num_rods)

        min_rod_length = self.field_widgets["min_rod_length_cm"]
        assert isinstance(min_rod_length, QDoubleSpinBox)
        min_rod_length.setValue(params.min_rod_length_cm)

        max_rod_length = self.field_widgets["max_rod_length_cm"]
        assert isinstance(max_rod_length, QDoubleSpinBox)
        max_rod_length.setValue(params.max_rod_length_cm)

        max_angle = self.field_widgets["max_angle_deviation_deg"]
        assert isinstance(max_angle, QDoubleSpinBox)
        max_angle.setValue(params.max_angle_deviation_deg)

        num_layers = self.field_widgets["num_layers"]
        assert isinstance(num_layers, QSpinBox)
        num_layers.setValue(params.num_layers)

        min_anchor_distance_vertical = self.field_widgets["min_anchor_distance_vertical_cm"]
        assert isinstance(min_anchor_distance_vertical, QDoubleSpinBox)
        min_anchor_distance_vertical.setValue(params.min_anchor_distance_vertical_cm)

        min_anchor_distance_other = self.field_widgets["min_anchor_distance_other_cm"]
        assert isinstance(min_anchor_distance_other, QDoubleSpinBox)
        min_anchor_distance_other.setValue(params.min_anchor_distance_other_cm)

        main_direction_min = self.field_widgets["main_direction_range_min_deg"]
        assert isinstance(main_direction_min, QDoubleSpinBox)
        main_direction_min.setValue(params.main_direction_range_min_deg)

        main_direction_max = self.field_widgets["main_direction_range_max_deg"]
        assert isinstance(main_direction_max, QDoubleSpinBox)
        main_direction_max.setValue(params.main_direction_range_max_deg)

        random_angle_deviation = self.field_widgets["random_angle_deviation_deg"]
        assert isinstance(random_angle_deviation, QDoubleSpinBox)
        random_angle_deviation.setValue(params.random_angle_deviation_deg)

        max_iterations = self.field_widgets["max_iterations"]
        assert isinstance(max_iterations, QSpinBox)
        max_iterations.setValue(params.max_iterations)

        max_duration = self.field_widgets["max_duration_sec"]
        assert isinstance(max_duration, QDoubleSpinBox)
        max_duration.setValue(params.max_duration_sec)

        max_eval_attempts = self.field_widgets["max_evaluation_attempts"]
        assert isinstance(max_eval_attempts, QSpinBox)
        max_eval_attempts.setValue(params.max_evaluation_attempts)

        max_eval_duration = self.field_widgets["max_evaluation_duration_sec"]
        assert isinstance(max_eval_duration, QDoubleSpinBox)
        max_eval_duration.setValue(params.max_evaluation_duration_sec)

        min_fitness = self.field_widgets["min_acceptable_fitness"]
        assert isinstance(min_fitness, QDoubleSpinBox)
        min_fitness.setValue(params.min_acceptable_fitness)

        infill_weight = self.field_widgets["infill_weight_per_meter_kg_m"]
        assert isinstance(infill_weight, QDoubleSpinBox)
        infill_weight.setValue(params.infill_weight_per_meter_kg_m)

        # Set evaluator type and parameters
        if params.evaluator is not None and self.evaluator_type_combo is not None:
            evaluator_type = params.evaluator.type  # 'type' field is the discriminator
            # Set combo box to correct evaluator type
            index = self.evaluator_type_combo.findText(evaluator_type)
            if index >= 0:
                self.evaluator_type_combo.setCurrentIndex(index)
            # Set evaluator parameters
            if evaluator_type in self.evaluator_widgets:
                self.evaluator_widgets[evaluator_type].set_parameters(params.evaluator)
