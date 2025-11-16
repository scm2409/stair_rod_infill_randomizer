"""Shape interface for railing frame geometries."""

from abc import ABC, abstractmethod

from shapely.geometry import Polygon

from railing_generator.domain.rod import Rod


class Shape(ABC):
    """
    Abstract base class defining the interface for railing frame shapes.

    All shape implementations must provide methods to:
    - Get frame rods (layer 0)
    - Get boundary polygon

    This uses ABC instead of Protocol because:
    - We control all shape implementations in this codebase
    - We want runtime enforcement of the interface contract
    - We may add shared behavior in the future
    """

    @abstractmethod
    def get_frame_rods(self) -> list[Rod]:
        """
        Get frame rods (layer 0) for the shape.

        Returns:
            List of Rod objects representing the frame
        """
        ...

    @abstractmethod
    def get_boundary(self) -> Polygon:
        """
        Get the boundary polygon of the shape.

        Returns:
            Shapely Polygon defining the frame boundary
        """
        ...
