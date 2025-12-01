"""Fitness update data model for manual editing."""

from pydantic import BaseModel


class FitnessUpdate(BaseModel):
    """
    Data class for fitness score updates after manual edits.

    Contains the old and new fitness scores along with the acceptability
    status of the new infill configuration.

    Attributes:
        old_score: Previous fitness score, or None if not available
        new_score: New fitness score after the edit, or None if not available
        is_acceptable: Whether the new infill is acceptable (no constraint violations)
    """

    old_score: float | None = None
    new_score: float | None = None
    is_acceptable: bool | None = None

    model_config = {"frozen": True}
