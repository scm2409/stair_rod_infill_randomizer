"""Factory for creating RailingShape instances from type strings."""

from railing_generator.domain.shapes.parallelogram_railing_shape import (
    ParallelogramRailingShape,
    ParallelogramRailingShapeParameters,
)
from railing_generator.domain.shapes.railing_shape import RailingShape
from railing_generator.domain.shapes.railing_shape_parameters import RailingShapeParameters
from railing_generator.domain.shapes.rectangular_railing_shape import (
    RectangularRailingShape,
    RectangularRailingShapeParameters,
)
from railing_generator.domain.shapes.staircase_railing_shape import (
    StaircaseRailingShape,
    StaircaseRailingShapeParameters,
)


class RailingShapeFactory:
    """
    Factory for creating RailingShape instances from type strings.

    This factory enables the extensible shape system by mapping type identifiers
    to concrete shape implementations.
    """

    # Map of shape type identifiers to shape classes
    _SHAPE_REGISTRY: dict[str, type[RailingShape]] = {
        "staircase": StaircaseRailingShape,
        "rectangular": RectangularRailingShape,
        "parallelogram": ParallelogramRailingShape,
    }

    @classmethod
    def create_shape(cls, shape_type: str, parameters: RailingShapeParameters) -> RailingShape:
        """
        Create a RailingShape instance from a type string and parameters.

        Args:
            shape_type: The shape type identifier (e.g., "staircase", "rectangular")
            parameters: The shape parameters (must match the shape type)

        Returns:
            A RailingShape instance of the appropriate type

        Raises:
            ValueError: If the shape type is not registered or parameters don't match
        """
        if shape_type not in cls._SHAPE_REGISTRY:
            available_types = ", ".join(cls._SHAPE_REGISTRY.keys())
            raise ValueError(
                f"Unknown shape type: '{shape_type}'. Available types: {available_types}"
            )

        # Validate that parameters match the expected type for this shape
        if shape_type == "staircase":
            if not isinstance(parameters, StaircaseRailingShapeParameters):
                raise ValueError(
                    f"Shape type 'staircase' requires StaircaseRailingShapeParameters, "
                    f"got {type(parameters).__name__}"
                )
            return StaircaseRailingShape(parameters)
        elif shape_type == "rectangular":
            if not isinstance(parameters, RectangularRailingShapeParameters):
                raise ValueError(
                    f"Shape type 'rectangular' requires RectangularRailingShapeParameters, "
                    f"got {type(parameters).__name__}"
                )
            return RectangularRailingShape(parameters)
        elif shape_type == "parallelogram":
            if not isinstance(parameters, ParallelogramRailingShapeParameters):
                raise ValueError(
                    f"Shape type 'parallelogram' requires ParallelogramRailingShapeParameters, "
                    f"got {type(parameters).__name__}"
                )
            return ParallelogramRailingShape(parameters)

        # This should never be reached if all shape types are handled above
        raise ValueError(f"Unhandled shape type: '{shape_type}'")

    @classmethod
    def get_available_shape_types(cls) -> list[str]:
        """
        Get a list of all available shape type identifiers.

        Returns:
            List of shape type strings
        """
        return list(cls._SHAPE_REGISTRY.keys())
