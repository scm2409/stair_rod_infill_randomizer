"""Parameter widgets for infill generators."""

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QSpinBox,
    QWidget,
)

from railing_generator.domain.infill_generators.random_generator_parameters import (
    RandomGeneratorDefaults,
    RandomGeneratorParameters,
)


class RandomGeneratorParameterWidget(QWidget):
    """
    Parameter widget for random generator configuration.

    Provides input fields for all random generator parameters with validation.
    """

    def __init__(self) -> None:
        """Initialize the random generator parameter widget."""
        super().__init__()

        # Load defaults
        self.defaults = RandomGeneratorDefaults()

        # Create UI
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the UI layout and widgets."""
        layout = QFormLayout(self)

        # Number of rods
        self.num_rods_spin = QSpinBox()
        self.num_rods_spin.setRange(1, 200)
        self.num_rods_spin.setValue(self.defaults.num_rods)
        self.num_rods_spin.setSuffix(" rods")
        layout.addRow("Number of Rods:", self.num_rods_spin)

        # Min rod length
        self.min_rod_length_spin = QDoubleSpinBox()
        self.min_rod_length_spin.setRange(1.0, 1000.0)
        self.min_rod_length_spin.setValue(self.defaults.min_rod_length_cm)
        self.min_rod_length_spin.setSuffix(" cm")
        self.min_rod_length_spin.setDecimals(1)
        layout.addRow("Min Rod Length:", self.min_rod_length_spin)

        # Max rod length
        self.max_rod_length_spin = QDoubleSpinBox()
        self.max_rod_length_spin.setRange(1.0, 1000.0)
        self.max_rod_length_spin.setValue(self.defaults.max_rod_length_cm)
        self.max_rod_length_spin.setSuffix(" cm")
        self.max_rod_length_spin.setDecimals(1)
        layout.addRow("Max Rod Length:", self.max_rod_length_spin)

        # Max angle deviation
        self.max_angle_spin = QDoubleSpinBox()
        self.max_angle_spin.setRange(0.0, 45.0)
        self.max_angle_spin.setValue(self.defaults.max_angle_deviation_deg)
        self.max_angle_spin.setSuffix(" °")
        self.max_angle_spin.setDecimals(1)
        layout.addRow("Max Angle Deviation:", self.max_angle_spin)

        # Number of layers
        self.num_layers_spin = QSpinBox()
        self.num_layers_spin.setRange(1, 5)
        self.num_layers_spin.setValue(self.defaults.num_layers)
        self.num_layers_spin.setSuffix(" layers")
        layout.addRow("Number of Layers:", self.num_layers_spin)

        # Min anchor distance
        self.min_anchor_distance_spin = QDoubleSpinBox()
        self.min_anchor_distance_spin.setRange(0.1, 100.0)
        self.min_anchor_distance_spin.setValue(self.defaults.min_anchor_distance_cm)
        self.min_anchor_distance_spin.setSuffix(" cm")
        self.min_anchor_distance_spin.setDecimals(1)
        layout.addRow("Min Anchor Distance:", self.min_anchor_distance_spin)

        # Max iterations
        self.max_iterations_spin = QSpinBox()
        self.max_iterations_spin.setRange(1, 10000)
        self.max_iterations_spin.setValue(self.defaults.max_iterations)
        layout.addRow("Max Iterations:", self.max_iterations_spin)

        # Max duration
        self.max_duration_spin = QDoubleSpinBox()
        self.max_duration_spin.setRange(0.1, 300.0)
        self.max_duration_spin.setValue(self.defaults.max_duration_sec)
        self.max_duration_spin.setSuffix(" sec")
        self.max_duration_spin.setDecimals(1)
        layout.addRow("Max Duration:", self.max_duration_spin)

        # Infill weight per meter
        self.infill_weight_spin = QDoubleSpinBox()
        self.infill_weight_spin.setRange(0.01, 10.0)
        self.infill_weight_spin.setValue(self.defaults.infill_weight_per_meter_kg_m)
        self.infill_weight_spin.setSuffix(" kg/m")
        self.infill_weight_spin.setDecimals(2)
        layout.addRow("Infill Weight/Meter:", self.infill_weight_spin)

    def get_parameters(self) -> RandomGeneratorParameters:
        """
        Get the current parameter values as a RandomGeneratorParameters instance.

        Returns:
            RandomGeneratorParameters with current widget values
        """
        return RandomGeneratorParameters(
            num_rods=self.num_rods_spin.value(),
            min_rod_length_cm=self.min_rod_length_spin.value(),
            max_rod_length_cm=self.max_rod_length_spin.value(),
            max_angle_deviation_deg=self.max_angle_spin.value(),
            num_layers=self.num_layers_spin.value(),
            min_anchor_distance_cm=self.min_anchor_distance_spin.value(),
            max_iterations=self.max_iterations_spin.value(),
            max_duration_sec=self.max_duration_spin.value(),
            infill_weight_per_meter_kg_m=self.infill_weight_spin.value(),
        )
