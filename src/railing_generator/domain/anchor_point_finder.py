"""Anchor point finder for manual rod editing."""

from shapely.geometry import Point

from railing_generator.domain.anchor_point import AnchorPoint


class AnchorPointFinder:
    """
    Finds anchor points within a search radius.

    This class is used during manual rod editing to find the nearest
    unconnected anchor point to a given position.

    Attributes:
        search_radius_cm: Maximum distance from search position to consider
    """

    def __init__(self, search_radius_cm: float = 10.0) -> None:
        """
        Initialize the anchor point finder.

        Args:
            search_radius_cm: Maximum search radius in centimeters (default: 10.0)
        """
        if search_radius_cm <= 0:
            raise ValueError("search_radius_cm must be positive")
        self.search_radius_cm = search_radius_cm

    def find_nearest_unconnected(
        self,
        position: Point,
        anchor_points: list[AnchorPoint],
    ) -> AnchorPoint | None:
        """
        Find the nearest unconnected anchor point within search radius.

        Args:
            position: Shapely Point of the search center
            anchor_points: List of all anchor points to search

        Returns:
            Nearest unconnected anchor point within search radius,
            or None if none found
        """
        if not anchor_points:
            return None
        nearest: AnchorPoint | None = None
        nearest_distance: float = float("inf")

        for anchor in anchor_points:
            # Skip connected (used) anchors
            if anchor.used:
                continue

            # Calculate distance using Shapely
            distance = position.distance(anchor.position)

            # Check if within search radius and closer than current nearest
            if distance <= self.search_radius_cm and distance < nearest_distance:
                nearest = anchor
                nearest_distance = distance

        return nearest

    def find_all_unconnected_within_radius(
        self,
        position: Point,
        anchor_points: list[AnchorPoint],
    ) -> list[tuple[AnchorPoint, float]]:
        """
        Find all unconnected anchor points within search radius.

        Args:
            position: Shapely Point of the search center
            anchor_points: List of all anchor points to search

        Returns:
            List of (anchor_point, distance) tuples sorted by distance,
            containing all unconnected anchors within search radius
        """
        if not anchor_points:
            return []
        results: list[tuple[AnchorPoint, float]] = []

        for anchor in anchor_points:
            # Skip connected (used) anchors
            if anchor.used:
                continue

            # Calculate distance using Shapely
            distance = position.distance(anchor.position)

            # Check if within search radius
            if distance <= self.search_radius_cm:
                results.append((anchor, distance))

        # Sort by distance (nearest first)
        results.sort(key=lambda x: x[1])
        return results
