"""UI settings configuration."""

from dataclasses import dataclass
from pathlib import Path

from omegaconf import OmegaConf


@dataclass
class ManualEditingSettings:
    """Settings for manual rod editing."""

    search_radius_cm: float = 10.0
    max_undo_history: int = 50


@dataclass
class UISettings:
    """UI settings loaded from configuration."""

    manual_editing: ManualEditingSettings


def load_ui_settings(config_path: Path | None = None) -> UISettings:
    """
    Load UI settings from configuration file.

    Args:
        config_path: Path to the configuration file. If None, uses default path.

    Returns:
        UISettings object with loaded configuration
    """
    if config_path is None:
        # Default path relative to project root
        config_path = Path("conf/ui/settings.yaml")

    if config_path.exists():
        cfg = OmegaConf.load(config_path)
        # Extract manual_editing section using OmegaConf.select for type safety
        manual_editing_cfg = OmegaConf.select(cfg, "manual_editing", default={})
        if manual_editing_cfg is None:
            manual_editing_cfg = {}

        # Get values with defaults
        search_radius = (
            manual_editing_cfg.get("search_radius_cm", 10.0)
            if isinstance(manual_editing_cfg, dict)
            else 10.0
        )
        max_history = (
            manual_editing_cfg.get("max_undo_history", 50)
            if isinstance(manual_editing_cfg, dict)
            else 50
        )

        # Handle OmegaConf DictConfig
        if hasattr(manual_editing_cfg, "get"):
            search_radius = manual_editing_cfg.get("search_radius_cm", 10.0)
            max_history = manual_editing_cfg.get("max_undo_history", 50)

        manual_editing = ManualEditingSettings(
            search_radius_cm=float(search_radius),
            max_undo_history=int(max_history),
        )
        return UISettings(manual_editing=manual_editing)
    else:
        # Return defaults if config file doesn't exist
        return UISettings(manual_editing=ManualEditingSettings())
