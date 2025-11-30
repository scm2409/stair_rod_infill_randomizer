"""Shared fixtures for presentation layer tests."""

import pytest
from pytestqt.qtbot import QtBot

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.presentation.main_window import MainWindow


@pytest.fixture
def project_model_for_ui() -> RailingProjectModel:
    """Create a RailingProjectModel for UI testing."""
    return RailingProjectModel()


@pytest.fixture
def controller_for_ui(project_model_for_ui: RailingProjectModel) -> ApplicationController:
    """Create an ApplicationController for UI testing."""
    return ApplicationController(project_model_for_ui)


@pytest.fixture
def main_window_no_confirm(
    qtbot: QtBot,
    project_model_for_ui: RailingProjectModel,
    controller_for_ui: ApplicationController,
) -> MainWindow:
    """
    Create a MainWindow for testing with close confirmation disabled.

    This fixture sets _skip_close_confirmation to True to prevent
    the unsaved changes dialog from appearing during test cleanup.
    """
    window = MainWindow(project_model_for_ui, controller_for_ui)
    window._skip_close_confirmation = True  # Prevent dialog on close
    qtbot.addWidget(window)
    return window
