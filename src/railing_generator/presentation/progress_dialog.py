"""Progress dialog for long-running operations."""

import logging

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class LogSignalProxy(QObject):
    """
    Proxy for thread-safe log message delivery to UI.

    This class acts as a bridge between logging handlers (which may be called
    from any thread) and Qt UI widgets (which must only be updated from the
    main thread). The proxy lives in the main thread and emits signals that
    Qt automatically queues when called from worker threads.
    """

    log_message = Signal(str)

    def __init__(self, parent: QObject | None = None):
        """
        Initialize the log signal proxy.

        Args:
            parent: Parent QObject (optional)
        """
        super().__init__(parent)

    def emit_log(self, message: str) -> None:
        """
        Emit a log message (thread-safe).

        This method can be called from any thread. Qt will automatically
        queue the signal if called from a different thread than the proxy's
        thread (which should be the main thread).

        Args:
            message: The log message to emit
        """
        self.log_message.emit(message)


class QTextEditLogHandler(logging.Handler):
    """
    Custom logging handler that writes to QTextEdit via signal proxy.

    This handler uses LogSignalProxy to ensure thread-safe delivery of log
    messages to the UI. The proxy emits signals that Qt automatically queues
    when called from worker threads, ensuring UI updates only happen in the
    main thread.
    """

    def __init__(self, log_proxy: LogSignalProxy):
        """
        Initialize the log handler.

        Args:
            log_proxy: The LogSignalProxy to emit log messages through
        """
        super().__init__()
        self.log_proxy = log_proxy

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record via the signal proxy.

        This method can be called from any thread. The proxy will handle
        thread-safe delivery to the UI.

        Args:
            record: The log record to emit
        """
        try:
            msg = self.format(record)
            # This is thread-safe: proxy will queue signal if needed
            self.log_proxy.emit_log(msg)
        except Exception:
            # Ignore errors (handler may be shutting down or proxy deleted)
            pass


class ProgressDialog(QDialog):
    """
    Modal progress dialog for long-running operations.

    This dialog:
    - Blocks input to the main window while visible
    - Shows real-time progress metrics (iteration, fitness, elapsed time)
    - Displays progress logs and logging messages
    - Provides a cancel/close button
    - Stays open after operation completes (user must close manually)

    Signals:
        cancel_requested: Emitted when the user clicks the cancel button
    """

    cancel_requested = Signal()

    def __init__(self, parent: QWidget | None = None, title: str = "Progress"):
        """
        Initialize the progress dialog.

        Args:
            parent: Parent widget (typically the main window)
            title: Window title for the dialog (default: "Progress")
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Create layout
        layout = QVBoxLayout()

        # Progress log text edit
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

        # Create log proxy (lives in main thread)
        self.log_proxy = LogSignalProxy(self)
        self.log_proxy.log_message.connect(self._append_log_message)

        # Set up logging handler to capture application logs
        self.log_handler = QTextEditLogHandler(self.log_proxy)
        self.log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.log_handler.setFormatter(formatter)

        # Add handler to the application logger
        logger = logging.getLogger("railing_generator")
        logger.addHandler(self.log_handler)

    @Slot(str)
    def _append_log_message(self, message: str) -> None:
        """
        Append log message to text edit (main thread only).

        This slot is connected to the log proxy's signal and ensures
        that all log messages are appended to the QTextEdit from the
        main thread, regardless of which thread the log message
        originated from.

        Limits the log to 10000 lines to prevent memory issues during
        very long operations.

        Args:
            message: The formatted log message to append
        """
        # Append the new message
        self.log_text.append(message)

        # Limit to 10000 lines to prevent memory issues
        max_lines = 10000
        document = self.log_text.document()
        if document.blockCount() > max_lines:
            # Remove oldest lines (from the beginning)
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            # Select and delete excess lines
            lines_to_remove = document.blockCount() - max_lines
            for _ in range(lines_to_remove):
                cursor.select(cursor.SelectionType.BlockUnderCursor)
                cursor.movePosition(cursor.MoveOperation.NextBlock, cursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # Remove the newline

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        """
        Handle dialog close event.

        Remove the log handler when dialog is closed.

        Args:
            event: The close event
        """
        logger = logging.getLogger(__name__)
        logger.debug("ProgressDialog.closeEvent() called - dialog is closing")
        # Remove the log handler
        railing_logger = logging.getLogger("railing_generator")
        railing_logger.removeHandler(self.log_handler)
        super().closeEvent(event)

    @Slot(dict)
    def update_progress(self, progress_data: dict) -> None:  # type: ignore[type-arg]
        """
        Update the progress display with new metrics.

        Args:
            progress_data: Dictionary containing progress information:
                - iteration: Current iteration number
                - best_fitness: Best fitness score found (or None)
                - elapsed_sec: Elapsed time in seconds
        """
        iteration = progress_data.get("iteration", 0)
        best_fitness = progress_data.get("best_fitness")
        elapsed_sec = progress_data.get("elapsed_sec", 0.0)

        # Add log entry
        log_entry = f"[{elapsed_sec:.1f}s] Iteration {iteration}"
        if best_fitness is not None:
            log_entry += f" - Fitness: {best_fitness:.4f}"
        self.log_text.append(log_entry)

    @Slot()
    def _on_cancel_clicked(self) -> None:
        """Handle cancel/close button click."""
        if self.cancel_button.text() == "Close":
            # User clicked Close after operation finished - just close the dialog
            self.accept()
        else:
            # User clicked Cancel during operation - request cancellation
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Cancelling...")
            self.cancel_requested.emit()

    @Slot(object)
    def on_operation_completed(self, result: object = None) -> None:
        """
        Handle operation completion.

        Changes the cancel button to "Close" and keeps dialog open.
        User must manually close the dialog.

        Args:
            result: The operation result (ignored, just for signal compatibility)
        """
        logger = logging.getLogger(__name__)
        logger.debug("ProgressDialog.on_operation_completed() called")
        self.log_text.append("\n=== Operation Completed Successfully ===")
        self.cancel_button.setText("Close")
        self.cancel_button.setEnabled(True)
        logger.debug("Button text changed to Close - user can click to close dialog")

    @Slot(str)
    def on_operation_failed(self, error_message: str) -> None:
        """
        Handle operation failure.

        Changes the cancel button to "Close" and keeps dialog open.
        User must manually close the dialog.

        Args:
            error_message: The error message to display
        """
        logger = logging.getLogger(__name__)
        logger.debug("ProgressDialog.on_operation_failed() called")
        self.log_text.append("\n=== Operation Failed ===")
        # Don't append the error message here - it's already in the logs
        self.cancel_button.setText("Close")
        self.cancel_button.setEnabled(True)
        logger.debug("Button text changed to Close - user can click to close dialog")
