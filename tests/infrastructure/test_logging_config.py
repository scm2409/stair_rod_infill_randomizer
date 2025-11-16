"""Tests for logging configuration."""

import logging
from pathlib import Path

import pytest

from railing_generator.infrastructure.logging_config import setup_logging


def test_setup_logging_creates_log_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that setup_logging creates a log file in the logs directory."""
    # Change to temporary directory
    monkeypatch.chdir(tmp_path)

    # Set up logging
    setup_logging(debug=False, verbose=False)

    # Verify logs directory was created
    log_dir = tmp_path / "logs"
    assert log_dir.exists()
    assert log_dir.is_dir()

    # Verify log file was created
    log_files = list(log_dir.glob("railing_*.log"))
    assert len(log_files) == 1
    assert log_files[0].exists()


def test_setup_logging_debug_level(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that debug flag sets log level to DEBUG."""
    monkeypatch.chdir(tmp_path)

    # Set up logging with debug=True
    setup_logging(debug=True, verbose=False)

    # Verify root logger level is DEBUG
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG


def test_setup_logging_info_level(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that without debug flag, log level is INFO."""
    monkeypatch.chdir(tmp_path)

    # Set up logging with debug=False
    setup_logging(debug=False, verbose=False)

    # Verify root logger level is INFO
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO


def test_setup_logging_file_handler_always_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that file handler is always added."""
    monkeypatch.chdir(tmp_path)

    # Set up logging without verbose
    setup_logging(debug=False, verbose=False)

    # Verify file handler exists
    root_logger = logging.getLogger()
    file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) >= 1


def test_setup_logging_console_handler_with_verbose(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that console handler is added when verbose=True."""
    monkeypatch.chdir(tmp_path)

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set up logging with verbose=True
    setup_logging(debug=False, verbose=True)

    # Verify we have at least 2 handlers (file + console)
    assert len(root_logger.handlers) >= 2


def test_setup_logging_hierarchical_loggers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that hierarchical loggers are configured."""
    monkeypatch.chdir(tmp_path)

    # Set up logging
    setup_logging(debug=True, verbose=False)

    # Verify hierarchical loggers exist and have correct level
    ui_logger = logging.getLogger("railing_generator.ui")
    assert ui_logger.level == logging.DEBUG

    shapes_logger = logging.getLogger("railing_generator.domain.shapes")
    assert shapes_logger.level == logging.DEBUG

    generators_logger = logging.getLogger("railing_generator.domain.generators")
    assert generators_logger.level == logging.DEBUG


def test_setup_logging_writes_to_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that log messages are written to the log file."""
    monkeypatch.chdir(tmp_path)

    # Set up logging
    setup_logging(debug=False, verbose=False)

    # Write a test log message
    test_logger = logging.getLogger("test")
    test_message = "Test log message for verification"
    test_logger.info(test_message)

    # Read log file and verify message was written
    log_dir = tmp_path / "logs"
    log_files = list(log_dir.glob("railing_*.log"))
    assert len(log_files) == 1

    log_content = log_files[0].read_text()
    assert test_message in log_content
