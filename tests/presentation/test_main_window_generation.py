"""Tests for main window generation integration."""

from unittest.mock import MagicMock, patch

from pytestqt.qtbot import QtBot

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.infill_generators.random_generator import RandomGenerator
from railing_generator.presentation.main_window import MainWindow


def test_main_window_handles_generation_started_signal(qtbot: QtBot) -> None:
    """Test that main window handles generation_started signal correctly without showing GUI."""
    # Create model and controller
    project_model = RailingProjectModel()
    controller = ApplicationController(project_model)

    # Create main window
    main_window = MainWindow(project_model, controller)
    main_window._skip_close_confirmation = True  # Prevent dialog on close during tests
    qtbot.addWidget(main_window)

    # Create a real generator instance
    generator = RandomGenerator()

    # Mock ProgressDialog to prevent it from showing
    with patch("railing_generator.presentation.main_window.ProgressDialog") as mock_dialog_class:
        mock_dialog_instance = MagicMock()
        mock_dialog_class.return_value = mock_dialog_instance

        # Emit the generation_started signal with a real generator
        # This should not raise an AttributeError about _abc_impl
        controller.generation_started.emit(generator)

        # Verify the dialog was created and shown (non-blocking)
        mock_dialog_class.assert_called_once_with(main_window, title="Generating Infill")
        mock_dialog_instance.show.assert_called_once()

        # Verify finished signal was connected to cleanup
        mock_dialog_instance.finished.connect.assert_called_once()


def test_main_window_generation_started_validates_generator_signals_directly(qtbot: QtBot) -> None:
    """Test that _on_generation_started validates generator has required signals."""
    # Create model and controller
    project_model = RailingProjectModel()
    controller = ApplicationController(project_model)

    # Create main window
    main_window = MainWindow(project_model, controller)
    main_window._skip_close_confirmation = True  # Prevent dialog on close during tests
    qtbot.addWidget(main_window)

    # Create a mock generator missing required signals
    mock_generator = MagicMock()
    # Remove one of the required signals
    del mock_generator.progress_updated

    # Call the method directly (not through signal) to test validation
    try:
        main_window._on_generation_started(mock_generator)
        assert False, "Expected TypeError for missing signal"
    except TypeError as e:
        assert "progress_updated" in str(e)
