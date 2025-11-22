"""Tests for QTextEditLogHandler."""

import logging

import pytest
from pytestqt.qtbot import QtBot

from railing_generator.presentation.progress_dialog import (
    LogSignalProxy,
    QTextEditLogHandler,
)


def test_qtextedit_log_handler_initialization(qtbot: QtBot) -> None:
    """Test that QTextEditLogHandler initializes with LogSignalProxy."""
    proxy = LogSignalProxy()
    handler = QTextEditLogHandler(proxy)

    assert handler.log_proxy is proxy


def test_qtextedit_log_handler_emit_formats_and_sends_message(qtbot: QtBot) -> None:
    """Test that handler formats log records and emits via proxy."""
    proxy = LogSignalProxy()
    handler = QTextEditLogHandler(proxy)
    handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

    messages_received: list[str] = []

    def capture_message(msg: str) -> None:
        messages_received.append(msg)

    proxy.log_message.connect(capture_message)

    # Create and emit a log record
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    handler.emit(record)

    # Process events to ensure signal is delivered
    qtbot.wait(10)

    # Verify message was formatted and emitted
    assert len(messages_received) == 1
    assert messages_received[0] == "INFO - Test message"


def test_qtextedit_log_handler_handles_exceptions_gracefully(qtbot: QtBot) -> None:
    """Test that handler ignores exceptions during shutdown."""
    proxy = LogSignalProxy()
    handler = QTextEditLogHandler(proxy)

    # Delete the proxy to simulate shutdown
    proxy.deleteLater()
    qtbot.wait(10)

    # Create a log record
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    # This should not raise an exception
    try:
        handler.emit(record)
    except Exception as e:
        pytest.fail(f"Handler should not raise exception during shutdown: {e}")


def test_qtextedit_log_handler_thread_safe_emission(qtbot: QtBot) -> None:
    """Test that handler can be called from any thread (via proxy)."""
    import threading

    proxy = LogSignalProxy()
    handler = QTextEditLogHandler(proxy)
    handler.setFormatter(logging.Formatter("%(message)s"))

    messages_received: list[str] = []

    def capture_message(msg: str) -> None:
        messages_received.append(msg)

    proxy.log_message.connect(capture_message)

    # Emit from a worker thread
    def worker_thread() -> None:
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Message from worker thread",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

    thread = threading.Thread(target=worker_thread)
    thread.start()
    thread.join()

    # Wait for signal to be processed
    qtbot.wait(100)

    # Verify message was received (Qt queued the signal)
    assert len(messages_received) == 1
    assert messages_received[0] == "Message from worker thread"
