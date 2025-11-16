"""Rod model for railing frame and infill elements."""

from typing import Any

from pydantic import BaseModel, Field, computed_field
from shapely.geometry import LineString, Point


class Rod(BaseModel):
    """
    Unified representation for frame and infill rods.
    Uses Shapely LineString for geometry operations.

    Attributes:
        geometry: Shapely LineString representing the rod's position
        start_cut_angle_deg: Cut angle at start point (-90 to 90 degrees)
        end_cut_angle_deg: Cut angle at end point (-90 to 90 degrees)
        weight_kg_m: Weight per meter in kilograms
        layer: Layer number (0=frame, >=1=infill)
    """

    geometry: LineString = Field(exclude=True)
    start_cut_angle_deg: float = Field(ge=-90, le=90, description="Cut angle at start point")
    end_cut_angle_deg: float = Field(ge=-90, le=90, description="Cut angle at end point")
    weight_kg_m: float = Field(gt=0, description="Weight per meter")
    layer: int = Field(ge=0, default=0, description="Layer (0=frame, >=1=infill)")

    model_config = {"arbitrary_types_allowed": True}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def length_cm(self) -> float:
        """Calculate rod length from geometry in centimeters."""
        return float(self.geometry.length)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def weight_kg(self) -> float:
        """Calculate rod weight from length and weight per meter."""
        return (self.length_cm / 100.0) * self.weight_kg_m

    @computed_field  # type: ignore[prop-decorator]
    @property
    def start_point(self) -> Point:
        """Get start point of rod."""
        return Point(self.geometry.coords[0])

    @computed_field  # type: ignore[prop-decorator]
    @property
    def end_point(self) -> Point:
        """Get end point of rod."""
        return Point(self.geometry.coords[-1])

    def to_bom_entry(self, rod_id: int) -> dict[str, Any]:
        """
        Convert rod to BOM table entry.

        Args:
            rod_id: Unique identifier for the rod

        Returns:
            Dictionary with BOM entry fields
        """
        return {
            "id": rod_id,
            "length_cm": round(self.length_cm, 2),
            "start_cut_angle_deg": round(self.start_cut_angle_deg, 1),
            "end_cut_angle_deg": round(self.end_cut_angle_deg, 1),
            "weight_kg": round(self.weight_kg, 3),
        }

    def model_dump_geometry(self) -> dict[str, Any]:
        """
        Serialize including geometry as coordinate list.

        Returns:
            Dictionary with all fields including geometry coordinates
        """
        data = self.model_dump()
        data["geometry"] = list(self.geometry.coords)
        return data
