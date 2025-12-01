"""Anchor point model for infill generation."""

from pydantic import BaseModel, Field, field_serializer, field_validator
from shapely.geometry import Point


class AnchorPoint(BaseModel):
    """
    Represents an anchor point on the frame boundary.

    Anchor points are potential attachment locations for infill rods on the
    frame boundary. They are generated during the infill generation process
    and assigned to layers.

    Attributes:
        position: Shapely Point with (x, y) coordinates of the anchor point
        frame_segment_index: Index of the frame rod this anchor is on
        is_vertical_segment: True if on a vertical frame rod, False otherwise
        frame_segment_angle_deg: Angle of the frame segment from vertical in degrees
        layer: Assigned layer number (1-indexed), None if unassigned
        used: True if this anchor has been used in a rod
    """

    position: Point
    frame_segment_index: int = Field(ge=0, description="Frame rod index")
    is_vertical_segment: bool = Field(description="True if on vertical frame rod")
    frame_segment_angle_deg: float = Field(
        description="Angle of frame segment from vertical in degrees"
    )
    layer: int | None = Field(default=None, ge=1, description="Assigned layer (1-indexed)")
    used: bool = Field(default=False, description="True if used in a rod")

    model_config = {"frozen": False, "arbitrary_types_allowed": True}

    @field_serializer("position")
    def serialize_position(self, point: Point) -> tuple[float, float]:
        """Serialize Point to coordinate tuple for JSON."""
        return (point.x, point.y)

    @field_validator("position", mode="before")
    @classmethod
    def parse_position(cls, v: Point | tuple[float, float] | list[float]) -> Point:
        """Parse position from Point, tuple, or list."""
        if isinstance(v, Point):
            return v
        if isinstance(v, (tuple, list)) and len(v) == 2:
            return Point(float(v[0]), float(v[1]))
        raise ValueError(f"Cannot parse position from {type(v)}")
