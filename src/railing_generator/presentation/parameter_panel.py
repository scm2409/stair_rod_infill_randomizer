"""Parameter panel for shape and generator configuration."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.infill_generators.generator_factory import GeneratorFactory
from railing_generator.domain.shapes.railing_shape_factory import RailingShapeFactory
from railing_generator.presentation.generator_parameter_widget import (
    RandomGeneratorParameterWidget,
)
from railing_generator.presentation.shape_parameter_widget import (
    RectangularParameterWidget,
    ShapeParameterWidget,
    StaircaseParameterWidget,
)


class ParameterPanel(QWidget):
    """
    Parameter panel for configuring shape and generator parameters.

    This panel provides:
    - Shape type selection dropdown
    - Dynamic parameter inputs based on selected shape
    - Update Shape button to render the frame
    """

    def __init__(
        self,
        project_model: RailingProjectModel,
        controller: ApplicationController,
    ) -> None:
        """
        Initialize the parameter panel.

        Args:
            project_model: The central state model to observe
            controller: The application controller for user actions
        """
        super().__init__()

        self.project_model = project_model
        self.controller = controller

        # Current parameter widgets
        self.current_shape_param_widget: ShapeParameterWidget | None = None
        self.current_generator_param_widget: RandomGeneratorParameterWidget | None = None

        # Create UI
        self._create_ui()

        # Connect to model signals
        self._connect_model_signals()

        # Initialize with first shape and generator type
        self._on_shape_type_changed(0)
        self._on_generator_type_changed(0)

    def _create_ui(self) -> None:
        """Create the UI layout and widgets."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Shape configuration group
        shape_group = self._create_shape_group()
        layout.addWidget(shape_group)

        # Update Shape button
        self.update_shape_button = QPushButton("Update Shape")
        self.update_shape_button.clicked.connect(self._on_update_shape_clicked)
        layout.addWidget(self.update_shape_button)

        # Generator configuration group
        generator_group = self._create_generator_group()
        layout.addWidget(generator_group)

        # Generate Infill button
        self.generate_infill_button = QPushButton("Generate Infill")
        self.generate_infill_button.clicked.connect(self._on_generate_infill_clicked)
        layout.addWidget(self.generate_infill_button)

    def _create_shape_group(self) -> QGroupBox:
        """Create the shape configuration group box."""
        group = QGroupBox("Shape Configuration")
        self.shape_group_layout = QVBoxLayout()

        # Shape type dropdown in a form layout
        type_layout = QFormLayout()
        self.shape_type_combo = QComboBox()
        available_types = RailingShapeFactory.get_available_shape_types()
        for shape_type in available_types:
            # Capitalize first letter for display
            display_name = shape_type.capitalize()
            self.shape_type_combo.addItem(display_name, shape_type)
        self.shape_type_combo.currentIndexChanged.connect(self._on_shape_type_changed)
        type_layout.addRow("Shape Type:", self.shape_type_combo)
        self.shape_group_layout.addLayout(type_layout)

        group.setLayout(self.shape_group_layout)
        return group

    def _create_generator_group(self) -> QGroupBox:
        """Create the generator configuration group box."""
        group = QGroupBox("Generator Configuration")
        self.generator_group_layout = QVBoxLayout()

        # Generator type dropdown in a form layout
        type_layout = QFormLayout()
        self.generator_type_combo = QComboBox()
        available_types = GeneratorFactory.get_available_generator_types()
        for generator_type in available_types:
            # Capitalize first letter for display
            display_name = generator_type.capitalize()
            self.generator_type_combo.addItem(display_name, generator_type)
        self.generator_type_combo.currentIndexChanged.connect(self._on_generator_type_changed)
        type_layout.addRow("Generator Type:", self.generator_type_combo)
        self.generator_group_layout.addLayout(type_layout)

        group.setLayout(self.generator_group_layout)
        return group

    def _on_shape_type_changed(self, index: int) -> None:
        """
        Handle shape type selection change.

        Args:
            index: The selected combo box index
        """
        # Remove existing parameter widget if any
        if self.current_shape_param_widget is not None:
            self.shape_group_layout.removeWidget(self.current_shape_param_widget)
            self.current_shape_param_widget.deleteLater()
            self.current_shape_param_widget = None

        # Get selected shape type
        shape_type = self.shape_type_combo.itemData(index)

        # Create appropriate parameter widget based on shape type
        if shape_type == "staircase":
            self.current_shape_param_widget = StaircaseParameterWidget()
        elif shape_type == "rectangular":
            self.current_shape_param_widget = RectangularParameterWidget()

        # Add the new widget to the layout
        if self.current_shape_param_widget is not None:
            self.shape_group_layout.addWidget(self.current_shape_param_widget)

    def _on_generator_type_changed(self, index: int) -> None:
        """
        Handle generator type selection change.

        Args:
            index: The selected combo box index
        """
        # Remove existing parameter widget if any
        if self.current_generator_param_widget is not None:
            self.generator_group_layout.removeWidget(self.current_generator_param_widget)
            self.current_generator_param_widget.deleteLater()
            self.current_generator_param_widget = None

        # Get selected generator type
        generator_type = self.generator_type_combo.itemData(index)

        # Create appropriate parameter widget based on generator type
        if generator_type == "random":
            self.current_generator_param_widget = RandomGeneratorParameterWidget()

        # Add the new widget to the layout
        if self.current_generator_param_widget is not None:
            self.generator_group_layout.addWidget(self.current_generator_param_widget)

    def _on_update_shape_clicked(self) -> None:
        """Handle Update Shape button click."""
        # Get selected shape type
        shape_type = self.shape_type_combo.currentData()

        # Get parameters from current widget
        if self.current_shape_param_widget is None:
            return

        params = self.current_shape_param_widget.get_parameters()

        # Update shape through controller
        self.controller.update_railing_shape(shape_type, params)

    def _on_generate_infill_clicked(self) -> None:
        """Handle Generate Infill button click."""
        # Get selected generator type
        generator_type = self.generator_type_combo.currentData()

        # Get parameters from current widget
        if self.current_generator_param_widget is None:
            return

        params = self.current_generator_param_widget.get_parameters()

        # Generate infill through controller
        try:
            self.controller.generate_infill(generator_type, params)
        except ValueError as e:
            # TODO: Show error dialog to user
            print(f"Error generating infill: {e}")

    def _connect_model_signals(self) -> None:
        """Connect to model signals for observing state changes."""
        # Currently no signals to observe for this panel
        # Future: Could observe shape type/parameters changes from model
        pass
