"""Rectangular-shaped railing frame implementation."""

from dataclasses import dataclass
from typing import Literal

from pydantic import Field
from shapely.geometry import LineString

from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.rod import Rod
from railing_generator.domain.shapes.railing_shape import RailingShape
from railing_generator.domain.shapes.railing_shape_parameters import (
    RailingShapeDefaults,
    RailingShapeParameters,
)


@dataclass
class RectangularRailingShapeDefaults(RailingShapeDefaults):
    """Default values for rectangular shape parameters (loaded from Hydra config)."""

    width_cm: float = 200.0
    height_cm: float = 100.0
    frame_weight_per_meter_kg_m: float = 0.5


class RectangularRailingShapeParameters(RailingShapeParameters):
    """Runtime parameters for rectangular shape with Pydantic validation."""

    type: Literal["rectangular"] = "rectangular"
    width_cm: float = Field(gt=0, description="Width in cm")
    height_cm: float = Field(gt=0, description="Height in cm")
    frame_weight_per_meter_kg_m: float = Field(gt=0, description="Frame weight per meter")

    @classmethod
    def from_defaults(
        cls, defaults: RectangularRailingShapeDefaults
    ) -> "RectangularRailingShapeParameters":
        """Create parameters from config defaults."""
        return cls(
            width_cm=defaults.width_cm,
            height_cm=defaults.height_cm,
            frame_weight_per_meter_kg_m=defaults.frame_weight_per_meter_kg_m,
        )


class RectangularRailingShape(RailingShape):
    """
    Rectangular-shaped railing frame configuration.

    This class represents the configuration for a rectangular-shaped railing frame.
    It generates an immutable RailingFrame containing the frame rods and boundary.

    Geometry:
    - Four straight sides forming a rectangle
    - Origin at bottom-left corner (0, 0)
    - Width extends along x-axis
    - Height extends along y-axis
    """

    def __init__(self, params: RectangularRailingShapeParameters):
        """
        Initialize rectangular shape configuration with validated parameters.

        Args:
            params: Validated rectangular shape parameters
        """
        self.params = params

    def generate_frame(self) -> RailingFrame:
        """
        Generate the railing frame for this configuration.

        Creates frame rods and returns them as an immutable RailingFrame.
        The boundary is automatically computed from the rods.

        Returns:
            Immutable RailingFrame containing frame rods (boundary computed automatically)
        """
        frame_rods = self._generate_frame_rods()
        return RailingFrame(rods=frame_rods)

    def _generate_frame_rods(self) -> list[Rod]:
        """
        Get frame rods (layer 0) for the rectangular shape.

        Rods are ordered to form a closed boundary loop (counterclockwise):
        1. Bottom edge (left to right)
        2. Right edge (bottom to top)
        3. Top edge (right to left)
        4. Left edge (top to bottom)

        Returns:
            List of Rod objects representing the frame
        """
        rods = []

        # 1. Bottom edge (left to right)
        bottom = Rod(
            geometry=LineString([(0.0, 0.0), (self.params.width_cm, 0.0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=self.params.frame_weight_per_meter_kg_m,
            layer=0,
        )
        rods.append(bottom)

        # 2. Right edge (bottom to top)
        right = Rod(
            geometry=LineString(
                [(self.params.width_cm, 0.0), (self.params.width_cm, self.params.height_cm)]
            ),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=self.params.frame_weight_per_meter_kg_m,
            layer=0,
        )
        rods.append(right)

        # 3. Top edge (right to left)
        top = Rod(
            geometry=LineString(
                [(self.params.width_cm, self.params.height_cm), (0.0, self.params.height_cm)]
            ),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=self.params.frame_weight_per_meter_kg_m,
            layer=0,
        )
        rods.append(top)

        # 4. Left edge (top to bottom)
        left = Rod(
            geometry=LineString([(0.0, self.params.height_cm), (0.0, 0.0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=self.params.frame_weight_per_meter_kg_m,
            layer=0,
        )
        rods.append(left)

        return rods
