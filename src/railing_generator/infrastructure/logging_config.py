"""Logging configuration using Rich for console output."""

import logging
from datetime import datetime
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(debug: bool = False, verbose: bool = False) -> None:
    """
    Configure application logging with file and optional console output.

    Args:
        debug: If True, set log level to DEBUG, otherwise INFO
        verbose: If True, also log to console (stdout)
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create log filename with current date
    log_file = log_dir / f"railing_{datetime.now().strftime('%Y-%m-%d')}.log"

    # Determine log level
    log_level = logging.DEBUG if debug else logging.INFO

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # File handler (always enabled)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler (only if verbose)
    if verbose:
        console_handler = RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=debug,
            show_time=True,
            show_path=debug,
        )
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

    # Set up hierarchical loggers
    # These can be configured with different levels later via Hydra config
    logging.getLogger("railing_generator.ui").setLevel(log_level)
    logging.getLogger("railing_generator.domain.shapes").setLevel(log_level)
    logging.getLogger("railing_generator.domain.generators").setLevel(log_level)
    logging.getLogger("railing_generator.domain.evaluator").setLevel(log_level)
    logging.getLogger("railing_generator.application").setLevel(log_level)

    # Log startup message
    root_logger.info("=" * 80)
    root_logger.info("Railing Infill Generator starting")
    root_logger.info(f"Log level: {'DEBUG' if debug else 'INFO'}")
    root_logger.info(f"Log file: {log_file}")
    root_logger.info("=" * 80)
