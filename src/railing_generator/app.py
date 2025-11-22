"""Application setup and initialization."""

import logging
from pathlib import Path

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.shapes.staircase_railing_shape import (
    StaircaseRailingShapeParameters,
)
from railing_generator.presentation.main_window import MainWindow

logger = logging.getLogger(__name__)


def create_main_window(config_path: Path) -> MainWindow:
    """
    Create and configure the main application window.

    Args:
        config_path: Path to configuration directory

    Returns:
        Configured main window instance
    """
    logger.info("Creating main window")
    logger.debug(f"Using config path: {config_path}")

    # TODO: Load Hydra configuration

    # Create central state model
    project_model = RailingProjectModel()

    # Create application controller
    controller = ApplicationController(project_model)

    # Create main window with model and controller
    window = MainWindow(project_model, controller)

    # TEMPORARY: Hard-code a StaircaseRailingShape for demonstration
    # This will be replaced with UI-driven shape creation
    params = StaircaseRailingShapeParameters(
        post_length_cm=120.0,
        stair_width_cm=280.0,
        stair_height_cm=150.0,
        num_steps=9,
        frame_weight_per_meter_kg_m=0.5,
    )

    # Use controller to update the shape (which will update model and notify observers)
    controller.update_railing_shape("staircase", params)

    # Fit view after frame is rendered
    window.viewport.fit_in_view()
    logger.info(
        f"Rendered RailingFrame with {project_model.railing_frame.rod_count if project_model.railing_frame else 0} frame rods"
    )

    logger.info("Main window created successfully")
    return window
