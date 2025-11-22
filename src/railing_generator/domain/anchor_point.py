"""Anchor point model for infill generation."""

from pydantic import BaseModel, Field


class AnchorPoint(BaseModel):
    """
    Represents an anchor point on the frame boundary.

    Anchor points are potential attachment locations for infill rods on the
    frame boundary. They are generated during the infill generation process
    and assigned to layers.

    Attributes:
        position: (x, y) coordinates of the anchor point
        frame_segment_index: Index of the frame rod this anchor is on
        is_vertical_segment: True if on a vertical frame rod, False otherwise
        layer: Assigned layer number (1-indexed), None if unassigned
        used: True if this anchor has been used in a rod
    """

    position: tuple[float, float] = Field(description="(x, y) coordinates")
    frame_segment_index: int = Field(ge=0, description="Frame rod index")
    is_vertical_segment: bool = Field(description="True if on vertical frame rod")
    layer: int | None = Field(default=None, ge=1, description="Assigned layer (1-indexed)")
    used: bool = Field(default=False, description="True if used in a rod")

    model_config = {"frozen": False}  # Mutable for internal generator use
