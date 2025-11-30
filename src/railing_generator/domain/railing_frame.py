"""Immutable container for railing frame rods and boundary."""

import shapely
from pydantic import BaseModel, Field, computed_field
from shapely.geometry import Polygon
from shapely.ops import polygonize

from railing_generator.domain.rod import Rod


class RailingFrame(BaseModel):
    """
    Immutable container for a railing frame.

    Contains the frame rods (layer 0) and the boundary polygon.
    This is the output of a RailingShape's generate_frame() method.

    Immutability ensures the frame cannot be accidentally modified after creation.
    """

    rods: list[Rod] = Field(description="Frame rods (layer 0)")

    model_config = {
        "arbitrary_types_allowed": True,  # Required for Shapely types
        "frozen": True,  # Make immutable
    }

    @computed_field  # type: ignore[prop-decorator]
    @property
    def boundary(self) -> Polygon:
        """
        Calculate the boundary polygon from frame rods.

        Uses shapely.polygonize which is independent of rod order.
        The boundary is computed from the rods, ensuring single source of truth.

        Returns:
            Shapely Polygon defining the frame boundary

        Raises:
            ValueError: If frame rods don't form exactly one closed polygon
        """
        # Extract geometries from all frame rods
        geometries = [rod.geometry for rod in self.rods]

        # Create a geometry collection and node it (add nodes at intersections)
        collection = shapely.GeometryCollection(geometries)
        noded = shapely.node(collection)

        # Polygonize to get the boundary polygon (order-independent)
        polygons = list(polygonize(noded.geoms))

        # Should result in exactly one polygon (the frame boundary)
        if len(polygons) != 1:
            raise ValueError(
                f"Expected exactly 1 polygon from frame rods, got {len(polygons)}. "
                "Frame rods may not form a closed boundary."
            )

        return polygons[0]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def enlarged_boundary(self) -> Polygon:
        """
        Calculate a slightly enlarged boundary polygon.

        Creates a boundary enlarged by 0.1cm (1mm) using buffer operation.
        This enlarged boundary can be used in algorithms to avoid rounding
        inconsistencies when checking if points are inside/outside the frame.

        Returns:
            Shapely Polygon that is 0.1cm larger than the actual boundary
        """
        return self.boundary.buffer(0.1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_length_cm(self) -> float:
        """Calculate total length of all frame rods."""
        return sum(rod.length_cm for rod in self.rods)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_weight_kg(self) -> float:
        """Calculate total weight of all frame rods."""
        return sum(rod.weight_kg for rod in self.rods)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rod_count(self) -> int:
        """Get the number of frame rods."""
        return len(self.rods)
