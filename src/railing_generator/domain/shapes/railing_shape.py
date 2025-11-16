"""RailingShape interface for railing frame geometries."""

from abc import ABC, abstractmethod

from railing_generator.domain.railing_frame import RailingFrame


class RailingShape(ABC):
    """
    Abstract base class defining the interface for railing frame shape configurations.

    A RailingShape represents the geometric configuration/type of a railing frame.
    It generates an immutable RailingFrame containing the frame rods and boundary.

    This uses ABC instead of Protocol because:
    - We control all shape implementations in this codebase
    - We want runtime enforcement of the interface contract
    - We may add shared behavior in the future
    """

    @abstractmethod
    def generate_frame(self) -> RailingFrame:
        """
        Generate the railing frame for this shape configuration.

        Returns:
            Immutable RailingFrame containing frame rods (layer 0) and boundary polygon
        """
        ...
