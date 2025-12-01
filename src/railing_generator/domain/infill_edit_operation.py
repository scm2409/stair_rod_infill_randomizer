"""Infill edit operation model for undo/redo support."""

from datetime import datetime

from pydantic import BaseModel, Field

from railing_generator.domain.railing_infill import RailingInfill


class InfillEditOperation(BaseModel):
    """
    Represents a single manual edit operation for undo/redo support.

    This class encapsulates the state before and after a manual rod edit,
    enabling undo and redo functionality. It follows the Command pattern.

    Attributes:
        previous_infill: The infill state before the edit
        new_infill: The infill state after the edit
        previous_fitness_score: Fitness score before the edit (None if no evaluator)
        new_fitness_score: Fitness score after the edit (None if no evaluator)
        source_anchor_index: Index of the source anchor point in the anchor list
        target_anchor_index: Index of the target anchor point in the anchor list
        rod_index: Index of the modified rod in the infill rods list
        timestamp: When the edit was performed
    """

    # State before the edit
    previous_infill: RailingInfill = Field(description="Infill state before the edit")
    previous_fitness_score: float | None = Field(
        default=None, description="Fitness score before edit (None if no evaluator)"
    )

    # State after the edit
    new_infill: RailingInfill = Field(description="Infill state after the edit")
    new_fitness_score: float | None = Field(
        default=None, description="Fitness score after edit (None if no evaluator)"
    )

    # Edit metadata
    source_anchor_index: int = Field(ge=0, description="Index of source anchor point")
    target_anchor_index: int = Field(ge=0, description="Index of target anchor point")
    rod_index: int = Field(ge=0, description="Index of modified rod")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the edit was performed"
    )

    model_config = {"frozen": True}

    @property
    def fitness_change(self) -> float | None:
        """
        Calculate the change in fitness score.

        Returns:
            The difference (new - previous), or None if either score is None
        """
        if self.previous_fitness_score is None or self.new_fitness_score is None:
            return None
        return self.new_fitness_score - self.previous_fitness_score

    @property
    def fitness_change_percent(self) -> float | None:
        """
        Calculate the percentage change in fitness score.

        Returns:
            The percentage change, or None if either score is None or previous is zero
        """
        if self.previous_fitness_score is None or self.new_fitness_score is None:
            return None
        if self.previous_fitness_score == 0:
            return None
        return (
            (self.new_fitness_score - self.previous_fitness_score)
            / self.previous_fitness_score
            * 100.0
        )
