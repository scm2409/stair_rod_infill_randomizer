"""Tests for the progress dialog."""

from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from railing_generator.presentation.progress_dialog import LogSignalProxy, ProgressDialog


def test_progress_dialog_initialization(qtbot: QtBot) -> None:
    """Test that the progress dialog initializes correctly."""
    dialog = ProgressDialog()
    qtbot.addWidget(dialog)

    # Verify window properties (default title is "Progress")
    assert dialog.windowTitle() == "Progress"
    assert dialog.isModal()
    assert dialog.minimumWidth() == 500
    assert dialog.minimumHeight() == 400

    # Verify widgets exist
    assert dialog.log_text is not None
    assert dialog.cancel_button is not None

    # Verify initial state
    assert dialog.cancel_button.text() == "Cancel"
    assert dialog.cancel_button.isEnabled()


def test_progress_dialog_custom_title(qtbot: QtBot) -> None:
    """Test that the progress dialog accepts a custom title."""
    dialog = ProgressDialog(title="Generating Infill")
    qtbot.addWidget(dialog)

    # Verify custom title
    assert dialog.windowTitle() == "Generating Infill"


def test_progress_dialog_update_progress(qtbot: QtBot) -> None:
    """Test that progress updates are displayed correctly."""
    dialog = ProgressDialog()
    qtbot.addWidget(dialog)

    # Update progress with iteration and elapsed time
    progress_data = {"iteration": 10, "best_fitness": None, "elapsed_sec": 1.5}
    dialog.update_progress(progress_data)

    # Verify log entry added
    log_text = dialog.log_text.toPlainText()
    assert "[1.5s] Iteration 10" in log_text


def test_progress_dialog_update_progress_with_fitness(qtbot: QtBot) -> None:
    """Test that progress updates with fitness score are displayed correctly."""
    dialog = ProgressDialog()
    qtbot.addWidget(dialog)

    # Update progress with fitness score
    progress_data = {"iteration": 25, "best_fitness": 0.8765, "elapsed_sec": 3.2}
    dialog.update_progress(progress_data)

    # Verify log entry includes fitness
    log_text = dialog.log_text.toPlainText()
    assert "[3.2s] Iteration 25" in log_text
    assert "Fitness: 0.8765" in log_text


def test_progress_dialog_cancel_button(qtbot: QtBot) -> None:
    """Test that the cancel button emits the cancel_requested signal."""
    dialog = ProgressDialog()
    qtbot.addWidget(dialog)

    # Connect to signal
    with qtbot.waitSignal(dialog.cancel_requested, timeout=1000):
        # Click cancel button
        qtbot.mouseClick(dialog.cancel_button, Qt.MouseButton.LeftButton)  # type: ignore[no-untyped-call]

    # Verify button state changed
    assert not dialog.cancel_button.isEnabled()
    assert dialog.cancel_button.text() == "Cancelling..."


def test_progress_dialog_operation_completed(qtbot: QtBot) -> None:
    """Test that operation completion changes button to Close but doesn't auto-close."""
    dialog = ProgressDialog()
    qtbot.addWidget(dialog)

    # Call completion handler (with None since we don't care about the result in this test)
    dialog.on_operation_completed(None)

    # Verify button changed to "Close"
    assert dialog.cancel_button.text() == "Close"
    assert dialog.cancel_button.isEnabled()

    # Verify completion message in log
    log_text = dialog.log_text.toPlainText()
    assert "Operation Completed Successfully" in log_text

    # Dialog should NOT auto-close (result should still be 0)
    assert dialog.result() == 0


def test_progress_dialog_operation_failed(qtbot: QtBot) -> None:
    """Test that operation failure is displayed correctly and doesn't auto-close."""
    dialog = ProgressDialog()
    qtbot.addWidget(dialog)

    # Call failure handler
    error_message = "Test error message"
    dialog.on_operation_failed(error_message)

    # Verify failure message in log (error details are in the logs, not duplicated)
    log_text = dialog.log_text.toPlainText()
    assert "Operation Failed" in log_text

    # Verify button state changed
    assert dialog.cancel_button.isEnabled()
    assert dialog.cancel_button.text() == "Close"

    # Dialog should NOT auto-close (result should still be 0)
    assert dialog.result() == 0


def test_progress_dialog_multiple_progress_updates(qtbot: QtBot) -> None:
    """Test that multiple progress updates accumulate in the log."""
    dialog = ProgressDialog()
    qtbot.addWidget(dialog)

    # Send multiple progress updates
    for i in range(1, 4):
        progress_data = {"iteration": i * 10, "best_fitness": None, "elapsed_sec": i * 1.0}
        dialog.update_progress(progress_data)

    # Verify all entries in log
    log_text = dialog.log_text.toPlainText()
    assert "[1.0s] Iteration 10" in log_text
    assert "[2.0s] Iteration 20" in log_text
    assert "[3.0s] Iteration 30" in log_text


def test_progress_dialog_captures_logging_messages(qtbot: QtBot) -> None:
    """Test that the dialog captures logging messages from the application."""
    import logging

    # Create dialog but don't add to qtbot yet (to prevent premature deletion)
    dialog = ProgressDialog()

    # Get the railing_generator logger (parent logger where handler is added)
    logger = logging.getLogger("railing_generator")
    original_level = logger.level
    logger.setLevel(logging.INFO)

    # Log a message while dialog is alive
    logger.info("Test log message from application")

    # Verify the message appears in the log text
    log_text = dialog.log_text.toPlainText()
    assert "Test log message from application" in log_text

    # Clean up - close dialog which removes the handler
    dialog.close()

    # Verify handler was removed
    assert dialog.log_handler not in logger.handlers

    # Restore original log level
    logger.setLevel(original_level)


def test_log_signal_proxy_initialization(qtbot: QtBot) -> None:
    """Test that LogSignalProxy initializes correctly."""
    proxy = LogSignalProxy()

    # Verify it's a QObject
    assert proxy is not None
    assert hasattr(proxy, "log_message")


def test_log_signal_proxy_emit_log(qtbot: QtBot) -> None:
    """Test that LogSignalProxy emits log messages correctly."""
    proxy = LogSignalProxy()

    # Connect to signal and verify emission
    with qtbot.waitSignal(proxy.log_message, timeout=1000) as blocker:
        proxy.emit_log("Test message")

    # Verify the signal was emitted with correct message
    assert blocker.args == ["Test message"]


def test_log_signal_proxy_multiple_messages(qtbot: QtBot) -> None:
    """Test that LogSignalProxy can emit multiple messages."""
    proxy = LogSignalProxy()

    messages_received: list[str] = []

    def capture_message(msg: str) -> None:
        messages_received.append(msg)

    proxy.log_message.connect(capture_message)

    # Emit multiple messages
    proxy.emit_log("Message 1")
    proxy.emit_log("Message 2")
    proxy.emit_log("Message 3")

    # Process events to ensure signals are delivered
    qtbot.wait(10)

    # Verify all messages were received
    assert messages_received == ["Message 1", "Message 2", "Message 3"]
