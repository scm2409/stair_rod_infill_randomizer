"""Parallelogram-shaped railing frame implementation."""

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
class ParallelogramRailingShapeDefaults(RailingShapeDefaults):
    """Default values for parallelogram shape parameters (loaded from Hydra config)."""

    post_length_cm: float = 100.0
    slope_width_cm: float = 300.0
    slope_height_cm: float = 150.0
    frame_weight_per_meter_kg_m: float = 0.5


class ParallelogramRailingShapeParameters(RailingShapeParameters):
    """Runtime parameters for parallelogram shape with Pydantic validation."""

    type: Literal["parallelogram"] = "parallelogram"
    post_length_cm: float = Field(gt=0, description="Post length in cm")
    slope_width_cm: float = Field(gt=0, description="Horizontal distance between posts in cm")
    slope_height_cm: float = Field(
        gt=0, description="Vertical rise from left to right post base in cm"
    )
    frame_weight_per_meter_kg_m: float = Field(gt=0, description="Frame weight per meter")

    @classmethod
    def from_defaults(
        cls, defaults: ParallelogramRailingShapeDefaults
    ) -> "ParallelogramRailingShapeParameters":
        """Create parameters from config defaults."""
        return cls(
            post_length_cm=defaults.post_length_cm,
            slope_width_cm=defaults.slope_width_cm,
            slope_height_cm=defaults.slope_height_cm,
            frame_weight_per_meter_kg_m=defaults.frame_weight_per_meter_kg_m,
        )


class ParallelogramRailingShape(RailingShape):
    """
    Parallelogram-shaped railing frame configuration.

    This class represents the configuration for a parallelogram-shaped railing frame.
    It generates an immutable RailingFrame containing the frame rods and boundary.

    Geometry:
    - Two vertical posts of equal length on left and right
    - slope_width_cm: horizontal distance between posts
    - slope_height_cm: vertical distance between post bases
    - Angled handrail connecting the tops of the posts
    - Angled bottom rail parallel to the handrail connecting the bases
    """

    def __init__(self, params: ParallelogramRailingShapeParameters):
        """
        Initialize parallelogram shape configuration with validated parameters.

        Args:
            params: Validated parallelogram shape parameters
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
        Get frame rods (layer 0) for the parallelogram shape.

        Rods are ordered to form a closed boundary loop (counterclockwise):
        1. Left post (vertical, going up)
        2. Handrail (angled from top-left to top-right)
        3. Right post (vertical, going down)
        4. Bottom rail (angled from bottom-right to bottom-left, parallel to handrail)

        Returns:
            List of Rod objects representing the frame
        """
        rods = []

        # Calculate key coordinates
        left_post_top_y = self.params.post_length_cm
        right_post_base_y = self.params.slope_height_cm
        right_post_top_y = self.params.slope_height_cm + self.params.post_length_cm

        # 1. Left post (vertical, going up from origin)
        left_post = Rod(
            geometry=LineString([(0.0, 0.0), (0.0, left_post_top_y)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=self.params.frame_weight_per_meter_kg_m,
            layer=0,
        )
        rods.append(left_post)

        # 2. Handrail (angled from top-left to top-right)
        handrail = Rod(
            geometry=LineString(
                [(0.0, left_post_top_y), (self.params.slope_width_cm, right_post_top_y)]
            ),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=self.params.frame_weight_per_meter_kg_m,
            layer=0,
        )
        rods.append(handrail)

        # 3. Right post (vertical, going down)
        right_post = Rod(
            geometry=LineString(
                [
                    (self.params.slope_width_cm, right_post_top_y),
                    (self.params.slope_width_cm, right_post_base_y),
                ]
            ),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=self.params.frame_weight_per_meter_kg_m,
            layer=0,
        )
        rods.append(right_post)

        # 4. Bottom rail (angled from bottom-right to bottom-left, parallel to handrail)
        bottom_rail = Rod(
            geometry=LineString([(self.params.slope_width_cm, right_post_base_y), (0.0, 0.0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=self.params.frame_weight_per_meter_kg_m,
            layer=0,
        )
        rods.append(bottom_rail)

        return rods
