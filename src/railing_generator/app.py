"""Application setup and initialization."""

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPen

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

    # TEMPORARY: Add a test square to demonstrate viewport functionality
    # This will be removed once shapes are implemented
    scene = window.viewport.scene()
    if scene is not None:
        pen = QPen(Qt.GlobalColor.blue, 2)
        scene.addRect(0, 0, 200, 200, pen)
        scene.addLine(0, 0, 200, 200, pen)
        scene.addLine(200, 0, 0, 200, pen)
        scene.addEllipse(50, 50, 100, 100, QPen(Qt.GlobalColor.red, 2))
        window.viewport.fit_in_view()
        logger.debug("Added temporary test shapes to viewport")

    logger.info("Main window created successfully")
    return window
