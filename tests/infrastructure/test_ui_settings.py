"""Tests for UI settings configuration."""

from pathlib import Path
import tempfile

import pytest

from railing_generator.infrastructure.ui_settings import (
    ManualEditingSettings,
    UISettings,
    load_ui_settings,
)


class TestManualEditingSettings:
    """Tests for ManualEditingSettings dataclass."""

    def test_default_values(self) -> None:
        """Test default values for manual editing settings."""
        settings = ManualEditingSettings()
        assert settings.search_radius_cm == 10.0
        assert settings.max_undo_history == 50

    def test_custom_values(self) -> None:
        """Test custom values for manual editing settings."""
        settings = ManualEditingSettings(search_radius_cm=15.0, max_undo_history=100)
        assert settings.search_radius_cm == 15.0
        assert settings.max_undo_history == 100


class TestUISettings:
    """Tests for UISettings dataclass."""

    def test_default_values(self) -> None:
        """Test default values for UI settings."""
        settings = UISettings(manual_editing=ManualEditingSettings())
        assert settings.manual_editing.search_radius_cm == 10.0
        assert settings.manual_editing.max_undo_history == 50


class TestLoadUISettings:
    """Tests for load_ui_settings function."""

    def test_load_from_default_path(self) -> None:
        """Test loading settings from default path."""
        # This test assumes conf/ui/settings.yaml exists
        settings = load_ui_settings()
        assert settings.manual_editing.search_radius_cm == 10.0
        assert settings.manual_editing.max_undo_history == 50

    def test_load_from_custom_path(self) -> None:
        """Test loading settings from custom path."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
manual_editing:
  search_radius_cm: 20.0
  max_undo_history: 100
"""
            )
            temp_path = Path(f.name)

        try:
            settings = load_ui_settings(temp_path)
            assert settings.manual_editing.search_radius_cm == 20.0
            assert settings.manual_editing.max_undo_history == 100
        finally:
            temp_path.unlink()

    def test_load_from_nonexistent_path(self) -> None:
        """Test loading settings from nonexistent path returns defaults."""
        settings = load_ui_settings(Path("/nonexistent/path/settings.yaml"))
        assert settings.manual_editing.search_radius_cm == 10.0
        assert settings.manual_editing.max_undo_history == 50

    def test_load_with_partial_config(self) -> None:
        """Test loading settings with partial config uses defaults for missing values."""
        # Create a temporary config file with only some values
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
manual_editing:
  search_radius_cm: 25.0
"""
            )
            temp_path = Path(f.name)

        try:
            settings = load_ui_settings(temp_path)
            assert settings.manual_editing.search_radius_cm == 25.0
            assert settings.manual_editing.max_undo_history == 50  # Default
        finally:
            temp_path.unlink()
