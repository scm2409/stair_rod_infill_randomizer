"""Persistable project state model for save/load operations."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from railing_generator.domain.anchor_point import AnchorPoint
from railing_generator.domain.infill_generators.random_generator_parameters import (
    RandomGeneratorParameters,
)
from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
    RandomGeneratorParametersV2,
)
from railing_generator.domain.rod import Rod
from railing_generator.domain.shapes.parallelogram_railing_shape import (
    ParallelogramRailingShapeParameters,
)
from railing_generator.domain.shapes.rectangular_railing_shape import (
    RectangularRailingShapeParameters,
)
from railing_generator.domain.shapes.staircase_railing_shape import (
    StaircaseRailingShapeParameters,
)


# Type aliases for discriminated unions
ShapeParametersUnion = Annotated[
    StaircaseRailingShapeParameters
    | RectangularRailingShapeParameters
    | ParallelogramRailingShapeParameters,
    Field(discriminator="type"),
]

GeneratorParametersUnion = Annotated[
    RandomGeneratorParameters | RandomGeneratorParametersV2,
    Field(discriminator="type"),
]


class UIState(BaseModel):
    """UI state that should be persisted."""

    rod_annotation_visible: bool = False
    infill_layers_colored_by_layer: bool = True


class PersistedFrame(BaseModel):
    """Persisted frame data."""

    rods: list[Rod]


class PersistedInfill(BaseModel):
    """Persisted infill data."""

    rods: list[Rod]
    fitness_score: float | None = None
    iteration_count: int | None = None
    duration_sec: float | None = None
    anchor_points: list[AnchorPoint] | None = None
    is_complete: bool = True


class PersistableProjectState(BaseModel):
    """
    Complete persistable project state.

    This model contains all data that should be saved/loaded from a project file.
    It uses Pydantic's built-in serialization for type-safe JSON conversion.

    Usage:
        # Save
        state = PersistableProjectState.from_project_model(model)
        json_str = state.model_dump_json(indent=2)

        # Load
        state = PersistableProjectState.model_validate_json(json_str)
        state.apply_to_project_model(model)
    """

    version: Literal["1.0"] = "1.0"

    # Shape configuration
    shape_type: str | None = None
    shape_parameters: ShapeParametersUnion | None = None

    # Generator configuration
    generator_type: str | None = None
    generator_parameters: GeneratorParametersUnion | None = None

    # Geometry data
    frame: PersistedFrame | None = None
    infill: PersistedInfill | None = None

    # UI state
    ui_state: UIState = Field(default_factory=UIState)
