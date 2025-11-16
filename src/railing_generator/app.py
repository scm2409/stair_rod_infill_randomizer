"""Application setup and initialization."""

import logging
from pathlib import Path

from railing_generator.domain.shapes.stair_shape import StairShape, StairShapeParameters
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
    # Create main window
    window = MainWindow()

    # TEMPORARY: Hard-code a StairShape for demonstration
    # This will be replaced with UI-driven shape creation
    params = StairShapeParameters(
        post_length_cm=120.0,
        stair_width_cm=280.0,
        stair_height_cm=150.0,
        num_steps=9,
        frame_weight_per_meter_kg_m=0.5,
    )
    shape = StairShape(params)

    # Set the shape and fit view
    window.viewport.set_shape(shape)
    window.viewport.fit_in_view()
    logger.info(f"Rendered StairShape with {len(shape.get_frame_rods())} frame rods")

    logger.info("Main window created successfully")
    return window
