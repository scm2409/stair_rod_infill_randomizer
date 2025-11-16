"""Shape implementations for railing frames."""

from railing_generator.domain.shapes.shape_interface import Shape
from railing_generator.domain.shapes.stair_shape import (
    StairShape,
    StairShapeDefaults,
    StairShapeParameters,
)

__all__ = [
    "Shape",
    "StairShape",
    "StairShapeDefaults",
    "StairShapeParameters",
]
