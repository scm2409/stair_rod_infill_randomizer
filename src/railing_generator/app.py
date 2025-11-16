"""Application setup and initialization."""

import logging
from pathlib import Path

from PySide6.QtWidgets import QMainWindow

logger = logging.getLogger(__name__)


def create_main_window(config_path: Path) -> QMainWindow:
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
    # TODO: Create main window with configuration
    # For now, create a placeholder window
    window = QMainWindow()
    window.setWindowTitle("Railing Infill Generator")
    window.resize(1200, 800)

    logger.info("Main window created successfully")
    return window
