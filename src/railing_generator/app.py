"""Application setup and initialization."""

import logging
from pathlib import Path

from railing_generator.domain.shapes.staircase_railing_shape import (
    StaircaseRailingShape,
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
    # Create main window
    window = MainWindow()

    # TEMPORARY: Hard-code a StaircaseRailingShape for demonstration
    # This will be replaced with UI-driven shape creation
    params = StaircaseRailingShapeParameters(
        post_length_cm=120.0,
        stair_width_cm=280.0,
        stair_height_cm=150.0,
        num_steps=9,
        frame_weight_per_meter_kg_m=0.5,
    )
    shape = StaircaseRailingShape(params)
    railing_frame = shape.generate_frame()

    # Set the railing frame and fit view
    window.viewport.set_railing_frame(railing_frame)
    window.viewport.fit_in_view()
    logger.info(f"Rendered RailingFrame with {railing_frame.rod_count} frame rods")

    logger.info("Main window created successfully")
    return window
