"""Rod model for railing frame and infill elements."""

from typing import Any
from pydantic import BaseModel, Field, computed_field, field_serializer, field_validator
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

    geometry: LineString
    start_cut_angle_deg: float = Field(ge=-90, le=90, description="Cut angle at start point")
    end_cut_angle_deg: float = Field(ge=-90, le=90, description="Cut angle at end point")
    weight_kg_m: float = Field(gt=0, description="Weight per meter")
    layer: int = Field(ge=0, default=0, description="Layer (0=frame, >=1=infill)")

    model_config = {"arbitrary_types_allowed": True}

    @field_serializer("geometry")
    def serialize_geometry(self, geom: LineString) -> list[list[float]]:
        """Serialize LineString to coordinate list for JSON."""
        return [list(coord) for coord in geom.coords]

    @field_validator("geometry", mode="before")
    @classmethod
    def parse_geometry(
        cls, v: LineString | list[list[float]] | list[tuple[float, float]]
    ) -> LineString:
        """Parse geometry from LineString or coordinate list."""
        if isinstance(v, LineString):
            return v
        if isinstance(v, list):
            return LineString(v)
        raise ValueError(f"Cannot parse geometry from {type(v)}")

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

    @property
    def start_point(self) -> Point:
        """Get start point of rod (not serialized - Shapely type)."""
        return Point(self.geometry.coords[0])

    @property
    def end_point(self) -> Point:
        """Get end point of rod (not serialized - Shapely type)."""
        return Point(self.geometry.coords[-1])

    @computed_field  # type: ignore[prop-decorator]
    @property
    def angle_from_vertical_deg(self) -> float:
        """
        Calculate the angle of this rod from vertical in degrees.

        This computed property calculates the signed angle deviation from vertical,
        independent of the LineString direction.

        Returns:
            Signed angle from vertical in degrees (-90 to +90)
            - 0° = perfectly vertical
            - Positive = leans right
            - Negative = leans left
            - ±90° = horizontal

        Note:
            This is the canonical property for calculating rod angles.
            - Generator uses abs(angle_from_vertical_deg) for constraint checking
            - Evaluator uses the signed value for distribution analysis
        """
        import math

        # Get coordinates
        coords = list(self.geometry.coords)
        x1, y1 = coords[0]
        x2, y2 = coords[-1]

        # Calculate dx and dy
        dx = x2 - x1
        dy = y2 - y1

        # Handle degenerate case
        if dx == 0 and dy == 0:
            return 0.0

        # Calculate signed angle from vertical
        # atan2(dx, dy) gives angle from vertical axis
        # Vertical (dy large, dx small) → angle near 0°
        # Horizontal (dx large, dy small) → angle near ±90°
        angle_rad = math.atan2(dx, dy)
        angle_deg = math.degrees(angle_rad)

        return angle_deg

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
