"""Railing infill model containing generated infill rods."""

from pydantic import BaseModel, Field, computed_field
from railing_generator.domain.rod import Rod


class RailingInfill(BaseModel):
    """
    Immutable container for infill rods and generation metadata.

    This class represents the result of an infill generation process,
    containing the generated rods and optional metadata about the generation.

    Attributes:
        rods: List of Rod objects representing the infill (layer >= 1)
        fitness_score: Optional fitness score from quality evaluation (higher = better)
        iteration_count: Optional number of iterations performed during generation
        duration_sec: Optional generation duration in seconds
    """

    rods: list[Rod] = Field(description="List of infill rods")
    fitness_score: float | None = Field(
        default=None, description="Optional fitness score (higher = better)"
    )
    iteration_count: int | None = Field(default=None, ge=0, description="Optional iteration count")
    duration_sec: float | None = Field(
        default=None, ge=0, description="Optional generation duration in seconds"
    )

    model_config = {"frozen": True}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rod_count(self) -> int:
        """Get the total number of infill rods."""
        return len(self.rods)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_length_cm(self) -> float:
        """Calculate total length of all infill rods in centimeters."""
        return sum(rod.length_cm for rod in self.rods)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_weight_kg(self) -> float:
        """Calculate total weight of all infill rods in kilograms."""
        return sum(rod.weight_kg for rod in self.rods)
