"""Application controller for orchestrating workflows and updating the model."""

from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.shapes.railing_shape_factory import RailingShapeFactory
from railing_generator.domain.shapes.railing_shape_parameters import RailingShapeParameters


class ApplicationController:
    """
    Application controller that orchestrates workflows and updates RailingProjectModel.

    This controller:
    - Creates domain objects (shapes, generators)
    - Orchestrates background threads for generation
    - Updates the model (never updates UI directly)
    - Handles serialization/deserialization for save/load

    The controller updates the model via setter methods, and the model emits signals
    to notify UI observers. This maintains clear separation between application logic
    and presentation.
    """

    def __init__(self, project_model: RailingProjectModel):
        """
        Initialize the application controller.

        Args:
            project_model: The central state model to update
        """
        self.project_model = project_model

    def create_new_project(self) -> None:
        """
        Create a new project by resetting the model to default state.

        This clears all state and emits signals to notify observers.
        """
        self.project_model.reset_to_defaults()

    def update_railing_shape(self, shape_type: str, parameters: RailingShapeParameters) -> None:
        """
        Update the railing shape by generating a new frame.

        This method:
        1. Creates a RailingShape instance from the type and parameters
        2. Generates the RailingFrame
        3. Updates the model with the new frame

        The model will emit signals to notify observers (e.g., viewport).

        Args:
            shape_type: The shape type identifier (e.g., "staircase")
            parameters: The validated shape parameters

        Raises:
            ValueError: If the shape type is unknown or parameters are invalid
        """
        # Update model with shape type and parameters
        self.project_model.set_railing_shape_type(shape_type)
        self.project_model.set_railing_shape_parameters(parameters)

        # Create shape instance and generate frame
        shape = RailingShapeFactory.create_shape(shape_type, parameters)
        frame = shape.generate_frame()

        # Update model with the generated frame
        self.project_model.set_railing_frame(frame)
