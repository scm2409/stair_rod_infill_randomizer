"""Entry point for the Railing Infill Generator application."""

import sys
from pathlib import Path

import typer
from PySide6.QtWidgets import QApplication

from railing_generator.infrastructure.logging_config import setup_logging

app = typer.Typer()


@app.command()
def main(
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Log to stdout"),
    config_path: Path = typer.Option(
        Path("conf"), "--config-path", help="Custom config directory"
    ),
) -> None:
    """Launch the Railing Infill Generator application."""
    # Set up logging first
    setup_logging(debug=debug, verbose=verbose)

    # Import here to avoid circular dependencies and ensure logging is configured
    from railing_generator.app import create_main_window

    # Create Qt application
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Railing Infill Generator")
    qt_app.setOrganizationName("RailingGenerator")

    # Create and show main window
    main_window = create_main_window(config_path=config_path)
    main_window.show()

    # Run application
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    app()
