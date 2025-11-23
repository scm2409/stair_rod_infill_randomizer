"""Parameter widget for Quality Evaluator."""

from PySide6.QtWidgets import QDoubleSpinBox

from railing_generator.domain.evaluators.quality_evaluator_criteria_defaults import (
    QualityEvaluatorCriteriaDefaults,
)
from railing_generator.domain.evaluators.quality_evaluator_parameters import (
    QualityEvaluatorParameters,
)
from railing_generator.presentation.evaluator_parameter_widget import EvaluatorParameterWidget


class QualityEvaluatorParameterWidget(EvaluatorParameterWidget):
    """
    Parameter widget for Quality Evaluator.

    Provides input controls for:
    - Maximum hole area threshold
    - Criteria weights (hole uniformity, incircle uniformity, angle distribution, anchor spacing)
    """

    def __init__(self) -> None:
        """Initialize with default values from configuration."""
        self._defaults = QualityEvaluatorCriteriaDefaults()
        super().__init__()

    def _create_widgets(self) -> None:
        """Create input widgets for Quality Evaluator parameters."""
        # Max hole area
        max_hole_area_spin = QDoubleSpinBox()
        max_hole_area_spin.setRange(0.1, 100000.0)
        max_hole_area_spin.setSuffix(" cm²")
        max_hole_area_spin.setDecimals(1)
        self.form_layout.addRow("Max Hole Area:", max_hole_area_spin)
        self.field_widgets["max_hole_area_cm2"] = max_hole_area_spin

        # Hole uniformity weight
        hole_uniformity_spin = QDoubleSpinBox()
        hole_uniformity_spin.setRange(0.0, 1.0)
        hole_uniformity_spin.setSingleStep(0.05)
        hole_uniformity_spin.setDecimals(2)
        self.form_layout.addRow("Hole Uniformity Weight:", hole_uniformity_spin)
        self.field_widgets["hole_uniformity_weight"] = hole_uniformity_spin

        # Incircle uniformity weight
        incircle_uniformity_spin = QDoubleSpinBox()
        incircle_uniformity_spin.setRange(0.0, 1.0)
        incircle_uniformity_spin.setSingleStep(0.05)
        incircle_uniformity_spin.setDecimals(2)
        self.form_layout.addRow("Incircle Uniformity Weight:", incircle_uniformity_spin)
        self.field_widgets["incircle_uniformity_weight"] = incircle_uniformity_spin

        # Angle distribution weight
        angle_distribution_spin = QDoubleSpinBox()
        angle_distribution_spin.setRange(0.0, 1.0)
        angle_distribution_spin.setSingleStep(0.05)
        angle_distribution_spin.setDecimals(2)
        self.form_layout.addRow("Angle Distribution Weight:", angle_distribution_spin)
        self.field_widgets["angle_distribution_weight"] = angle_distribution_spin

        # Anchor spacing horizontal weight
        anchor_spacing_h_spin = QDoubleSpinBox()
        anchor_spacing_h_spin.setRange(0.0, 1.0)
        anchor_spacing_h_spin.setSingleStep(0.05)
        anchor_spacing_h_spin.setDecimals(2)
        self.form_layout.addRow("Anchor Spacing Horizontal Weight:", anchor_spacing_h_spin)
        self.field_widgets["anchor_spacing_horizontal_weight"] = anchor_spacing_h_spin

        # Anchor spacing vertical weight
        anchor_spacing_v_spin = QDoubleSpinBox()
        anchor_spacing_v_spin.setRange(0.0, 1.0)
        anchor_spacing_v_spin.setSingleStep(0.05)
        anchor_spacing_v_spin.setDecimals(2)
        self.form_layout.addRow("Anchor Spacing Vertical Weight:", anchor_spacing_v_spin)
        self.field_widgets["anchor_spacing_vertical_weight"] = anchor_spacing_v_spin

    def _load_defaults(self) -> None:
        """Load default values into the widgets."""
        # Max hole area (default: 10000 cm²)
        widget = self.field_widgets["max_hole_area_cm2"]
        assert isinstance(widget, QDoubleSpinBox)
        widget.setValue(10000.0)

        # Hole uniformity weight
        widget = self.field_widgets["hole_uniformity_weight"]
        assert isinstance(widget, QDoubleSpinBox)
        widget.setValue(self._defaults.hole_uniformity_weight)

        # Incircle uniformity weight
        widget = self.field_widgets["incircle_uniformity_weight"]
        assert isinstance(widget, QDoubleSpinBox)
        widget.setValue(self._defaults.incircle_uniformity_weight)

        # Angle distribution weight
        widget = self.field_widgets["angle_distribution_weight"]
        assert isinstance(widget, QDoubleSpinBox)
        widget.setValue(self._defaults.angle_distribution_weight)

        # Anchor spacing horizontal weight
        widget = self.field_widgets["anchor_spacing_horizontal_weight"]
        assert isinstance(widget, QDoubleSpinBox)
        widget.setValue(self._defaults.anchor_spacing_horizontal_weight)

        # Anchor spacing vertical weight
        widget = self.field_widgets["anchor_spacing_vertical_weight"]
        assert isinstance(widget, QDoubleSpinBox)
        widget.setValue(self._defaults.anchor_spacing_vertical_weight)

    def _connect_validation_signals(self) -> None:
        """Connect valueChanged signals for real-time validation."""
        for widget in self.field_widgets.values():
            if isinstance(widget, QDoubleSpinBox):
                widget.valueChanged.connect(self._validate_and_update_ui)

    def get_parameters(self) -> QualityEvaluatorParameters:
        """
        Get the current parameter values as a validated Pydantic model.

        Returns:
            Validated QualityEvaluatorParameters

        Raises:
            ValidationError: If parameters are invalid
        """
        # Extract values from widgets
        widget = self.field_widgets["max_hole_area_cm2"]
        assert isinstance(widget, QDoubleSpinBox)
        max_hole_area_cm2 = widget.value()

        widget = self.field_widgets["hole_uniformity_weight"]
        assert isinstance(widget, QDoubleSpinBox)
        hole_uniformity_weight = widget.value()

        widget = self.field_widgets["incircle_uniformity_weight"]
        assert isinstance(widget, QDoubleSpinBox)
        incircle_uniformity_weight = widget.value()

        widget = self.field_widgets["angle_distribution_weight"]
        assert isinstance(widget, QDoubleSpinBox)
        angle_distribution_weight = widget.value()

        widget = self.field_widgets["anchor_spacing_horizontal_weight"]
        assert isinstance(widget, QDoubleSpinBox)
        anchor_spacing_horizontal_weight = widget.value()

        widget = self.field_widgets["anchor_spacing_vertical_weight"]
        assert isinstance(widget, QDoubleSpinBox)
        anchor_spacing_vertical_weight = widget.value()

        # Create and return validated parameters
        return QualityEvaluatorParameters(
            max_hole_area_cm2=max_hole_area_cm2,
            hole_uniformity_weight=hole_uniformity_weight,
            incircle_uniformity_weight=incircle_uniformity_weight,
            angle_distribution_weight=angle_distribution_weight,
            anchor_spacing_horizontal_weight=anchor_spacing_horizontal_weight,
            anchor_spacing_vertical_weight=anchor_spacing_vertical_weight,
        )
