"""Staircase-shaped railing frame implementation."""

from dataclasses import dataclass

from pydantic import BaseModel, Field, computed_field
from shapely.geometry import LineString

from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.rod import Rod
from railing_generator.domain.shapes.railing_shape import RailingShape


@dataclass
class StaircaseRailingShapeDefaults:
    """Default values for staircase shape parameters (loaded from Hydra config)."""

    post_length_cm: float = 150.0
    stair_width_cm: float = 280.0
    stair_height_cm: float = 280.0
    num_steps: int = 10
    frame_weight_per_meter_kg_m: float = 0.5


class StaircaseRailingShapeParameters(BaseModel):
    """Runtime parameters for staircase shape with Pydantic validation."""

    post_length_cm: float = Field(gt=0, description="Post length in cm")
    stair_width_cm: float = Field(gt=0, description="Stair width (horizontal distance) in cm")
    stair_height_cm: float = Field(gt=0, description="Stair height (vertical distance) in cm")
    num_steps: int = Field(ge=1, le=50, description="Number of steps")
    frame_weight_per_meter_kg_m: float = Field(gt=0, description="Frame weight per meter")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def step_width_cm(self) -> float:
        """Calculate step width from stair width and number of steps."""
        return self.stair_width_cm / self.num_steps

    @computed_field  # type: ignore[prop-decorator]
    @property
    def step_height_cm(self) -> float:
        """Calculate step height from stair height and number of steps."""
        return self.stair_height_cm / self.num_steps

    @classmethod
    def from_defaults(cls, defaults: StaircaseRailingShapeDefaults) -> "StaircaseRailingShapeParameters":
        """Create parameters from config defaults."""
        return cls(
            post_length_cm=defaults.post_length_cm,
            stair_width_cm=defaults.stair_width_cm,
            stair_height_cm=defaults.stair_height_cm,
            num_steps=defaults.num_steps,
            frame_weight_per_meter_kg_m=defaults.frame_weight_per_meter_kg_m,
        )


class StaircaseRailingShape(RailingShape):
    """
    Staircase-shaped railing frame configuration.

    This class represents the configuration for a staircase-shaped railing frame.
    It generates an immutable RailingFrame containing the frame rods and boundary.

    Geometry:
    - Two vertical posts of equal length on left and right
    - stair_width_cm: horizontal distance between posts
    - stair_height_cm: vertical distance between post bases
    - Angled handrail connecting the tops of the posts
    - Stepped bottom boundary following stair steps
    """

    def __init__(self, params: StaircaseRailingShapeParameters):
        """
        Initialize staircase shape configuration with validated parameters.

        Args:
            params: Validated staircase shape parameters
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
        Get frame rods (layer 0) for the stair shape.

        Rods are ordered to form a closed boundary loop (counterclockwise).

        Returns:
            List of Rod objects representing the frame
        """
        rods = []
        right_post_top_y = self.params.post_length_cm + self.params.stair_height_cm
        step_width_cm = self.params.stair_width_cm / self.params.num_steps
        step_height_cm = self.params.stair_height_cm / self.params.num_steps

        # 1. Left post (vertical, going up)
        left_post = Rod(
            geometry=LineString([(0.0, 0.0), (0.0, self.params.post_length_cm)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=self.params.frame_weight_per_meter_kg_m,
            layer=0,
        )
        rods.append(left_post)

        # 2. Handrail (angled from top-left to top-right)
        handrail = Rod(
            geometry=LineString(
                [(0.0, self.params.post_length_cm), (self.params.stair_width_cm, right_post_top_y)]
            ),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=self.params.frame_weight_per_meter_kg_m,
            layer=0,
        )
        rods.append(handrail)

        # 3. Right post (vertical, going down to stair_height)
        right_post = Rod(
            geometry=LineString(
                [
                    (self.params.stair_width_cm, right_post_top_y),
                    (self.params.stair_width_cm, self.params.stair_height_cm),
                ]
            ),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=self.params.frame_weight_per_meter_kg_m,
            layer=0,
        )
        rods.append(right_post)

        # 4. Steps (bottom boundary, going left from right to left)
        # Start from the base of the right post (at stair_height) and work left
        for i in range(self.params.num_steps - 1, -1, -1):
            x_right = (i + 1) * step_width_cm
            x_left = i * step_width_cm
            y = i * step_height_cm

            # First step from right post: vertical riser from stair_height down to top of highest step
            if i == self.params.num_steps - 1:
                y_top_step = (self.params.num_steps - 1) * step_height_cm
                if self.params.stair_height_cm > y_top_step:
                    first_riser = Rod(
                        geometry=LineString(
                            [
                                (self.params.stair_width_cm, self.params.stair_height_cm),
                                (x_right, y),
                            ]
                        ),
                        start_cut_angle_deg=0.0,
                        end_cut_angle_deg=0.0,
                        weight_kg_m=self.params.frame_weight_per_meter_kg_m,
                        layer=0,
                    )
                    rods.append(first_riser)

            # Horizontal tread (going left)
            step_horizontal = Rod(
                geometry=LineString([(x_right, y), (x_left, y)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=self.params.frame_weight_per_meter_kg_m,
                layer=0,
            )
            rods.append(step_horizontal)

            # Vertical riser (going down to next step) - skip for last step
            if i > 0:
                y_next = (i - 1) * step_height_cm
                step_vertical = Rod(
                    geometry=LineString([(x_left, y), (x_left, y_next)]),
                    start_cut_angle_deg=0.0,
                    end_cut_angle_deg=0.0,
                    weight_kg_m=self.params.frame_weight_per_meter_kg_m,
                    layer=0,
                )
                rods.append(step_vertical)

        return rods
