"""Entry point for the Railing Infill Generator application."""

import sys
from pathlib import Path

import typer

app = typer.Typer(help="Railing Infill Generator - Desktop application for generating rod arrangements")


@app.command()
def main(
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Log to stdout"),
    config_path: Path = typer.Option(
        Path("conf"), "--config-path", help="Custom config directory"
    ),
) -> None:
    """
    Launch the Railing Infill Generator application.
    
    This desktop application generates rod arrangements for railing frames
    with support for multiple shapes and generation algorithms.
    """
    # Import here to avoid loading Qt and other heavy dependencies for --help
    from PySide6.QtWidgets import QApplication
    
    from railing_generator.app import create_main_window
    from railing_generator.infrastructure.logging_config import setup_logging

    # Set up logging
    setup_logging(debug=debug, verbose=verbose)

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
