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
from railing_generator.domain.shapes.railing_shape_factory import RailingShapeFactory
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

        # Current parameter widget
        self.current_param_widget: ShapeParameterWidget | None = None

        # Create UI
        self._create_ui()

        # Connect to model signals
        self._connect_model_signals()

        # Initialize with first shape type
        self._on_shape_type_changed(0)

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

    def _on_shape_type_changed(self, index: int) -> None:
        """
        Handle shape type selection change.

        Args:
            index: The selected combo box index
        """
        # Remove existing parameter widget if any
        if self.current_param_widget is not None:
            self.shape_group_layout.removeWidget(self.current_param_widget)
            self.current_param_widget.deleteLater()
            self.current_param_widget = None

        # Get selected shape type
        shape_type = self.shape_type_combo.itemData(index)

        # Create appropriate parameter widget based on shape type
        if shape_type == "staircase":
            self.current_param_widget = StaircaseParameterWidget()
        elif shape_type == "rectangular":
            self.current_param_widget = RectangularParameterWidget()

        # Add the new widget to the layout
        if self.current_param_widget is not None:
            self.shape_group_layout.addWidget(self.current_param_widget)

    def _on_update_shape_clicked(self) -> None:
        """Handle Update Shape button click."""
        # Get selected shape type
        shape_type = self.shape_type_combo.currentData()

        # Get parameters from current widget
        if self.current_param_widget is None:
            return

        params = self.current_param_widget.get_parameters()

        # Update shape through controller
        self.controller.update_railing_shape(shape_type, params)

    def _connect_model_signals(self) -> None:
        """Connect to model signals for observing state changes."""
        # Currently no signals to observe for this panel
        # Future: Could observe shape type/parameters changes from model
        pass
