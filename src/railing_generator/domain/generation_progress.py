"""Generation progress data model."""

from pydantic import BaseModel, Field


class GenerationProgress(BaseModel):
    """
    Progress information for ongoing infill generation.

    This model tracks only the transient progress state (iteration and elapsed time).
    Fitness score is NOT stored here to avoid duplication - it comes from RailingInfill.

    Design rationale:
    - RailingInfill already stores fitness_score, iteration_count, and duration_sec
    - GenerationProgress only tracks current progress during generation
    - After generation completes, all data comes from RailingInfill (single source of truth)

    Attributes:
        iteration: Current iteration/attempt number
        elapsed_sec: Elapsed time in seconds since generation started
    """

    iteration: int = Field(default=0, ge=0, description="Current iteration number")
    elapsed_sec: float = Field(default=0.0, ge=0.0, description="Elapsed time in seconds")

    model_config = {"frozen": True}  # Immutable

    def to_status_message(self, prefix: str = "", fitness: float | None = None) -> str:
        """
        Format progress as a status bar message.

        Args:
            prefix: Optional prefix (e.g., "Completed", "Failed")
            fitness: Optional fitness score (from RailingInfill, not stored in this object)

        Returns:
            Formatted status message with iteration, fitness (if provided), and elapsed time
        """
        parts = []
        if prefix:
            parts.append(prefix)

        parts.append(f"Iteration {self.iteration}")

        if fitness is not None:
            parts.append(f"Fitness {fitness:.4f}")

        parts.append(f"Elapsed {self.elapsed_sec:.1f}s")

        return " | ".join(parts)
