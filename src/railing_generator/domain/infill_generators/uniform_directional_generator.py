"""Uniform Directional Generator implementation.

A deterministic infill generator that creates evenly distributed rod arrangements
across configurable layers with fixed directional control.
"""

import logging

from shapely.geometry import LineString, Point, Polygon

from railing_generator.domain.anchor_point import AnchorPoint
from railing_generator.domain.infill_generators.generator import Generator
from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorParameters,
)
from railing_generator.domain.infill_generators.uniform_directional_generator_parameters import (
    UniformDirectionalGeneratorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod

logger = logging.getLogger(__name__)


class UniformDirectionalGenerator(Generator):
    """
    Deterministic infill generator with evenly distributed rods across configurable layers.

    Key characteristics:
    - Deterministic: Identical inputs always produce identical outputs
    - Direct Calculation: No iteration or random number generation
    - Uniform Distribution: Evenly spaced anchors and rods
    - Layered Directions: Each layer has a fixed main direction from a configurable range
    - Fail-Fast: Fails immediately if constraints cannot be satisfied
    """

    # Define the parameter type for this generator
    PARAMETER_TYPE = UniformDirectionalGeneratorParameters

    def __init__(self) -> None:
        """Initialize the uniform directional generator."""
        super().__init__()

    def generate(self, frame: RailingFrame, params: InfillGeneratorParameters) -> RailingInfill:
        """
        Generate deterministic uniform infill arrangement within the frame.

        This is a deterministic generator that produces identical results given
        the same input parameters and frame geometry. It uses direct calculation
        (no random number generation) to place rods evenly across configurable layers.

        Algorithm:
        1. Validate parameter type
        2. Create evaluator from nested parameters
        3. Phase 1: Generate anchor grid (evenly spaced along boundary)
        4. Phase 2: Calculate layer directions (linear interpolation across range)
        5. Phase 3-4: Generate rods for each layer using line pattern snapping
        6. Verify rod count matches requested (fail if insufficient)
        7. Run evaluator and set fitness score
        8. Emit signals and return result

        Args:
            frame: The railing frame defining the boundary
            params: UniformDirectionalGeneratorParameters for generation

        Returns:
            RailingInfill containing the generated rods

        Raises:
            ValueError: If parameters are not UniformDirectionalGeneratorParameters
            RuntimeError: If generation fails (e.g., constraints cannot be satisfied)

        Requirements: 1.1, 1.2, 1.5, 4.2, 4.3, 7.1, 7.2, 7.3, 9.3
        """
        import time

        from railing_generator.domain.evaluators.evaluator_factory import EvaluatorFactory
        from railing_generator.domain.generation_progress import GenerationProgress

        # Validate and narrow parameter type (runtime check for type safety)
        if not isinstance(params, UniformDirectionalGeneratorParameters):
            raise ValueError(
                f"UniformDirectionalGenerator requires UniformDirectionalGeneratorParameters, "
                f"got {type(params).__name__}"
            )

        # Reset cancellation flag
        self.reset_cancellation()

        # Create evaluator from nested parameters (Requirements 7.1)
        evaluator = EvaluatorFactory.create_evaluator(params.evaluator)

        start_time = time.time()

        logger.info(
            f"Starting uniform directional generation: "
            f"num_rods={params.num_rods}, num_layers={params.num_layers}, "
            f"direction_range=[{params.main_direction_range_min_deg}°, "
            f"{params.main_direction_range_max_deg}°]"
        )

        # Emit initial progress
        progress = GenerationProgress(iteration=0, elapsed_sec=0.0)
        self.progress_updated.emit(progress)

        # Phase 1: Generate anchor grid (Requirements 3.1, 3.2, 3.4)
        anchor_points = self._generate_anchor_grid(frame, params)

        # Check if we have enough anchors for the requested rods
        # Each rod needs 2 anchors
        required_anchors = params.num_rods * 2
        if len(anchor_points) < required_anchors:
            error_msg = (
                f"Frame cannot accommodate {params.num_rods} rods with "
                f"{params.min_anchor_distance_cm}cm spacing. "
                f"Available anchors: {len(anchor_points)}, required: {required_anchors}"
            )
            logger.error(error_msg)
            self.generation_failed.emit(error_msg)
            raise RuntimeError(error_msg)

        # Phase 2: Calculate layer directions (Requirements 2.4, 2.5)
        layer_directions = self._calculate_layer_directions(params)

        # Calculate rods per layer (Requirements 1.2, 1.5, 4.2, 4.3)
        # Distribute evenly, with extra rods going to lower-numbered layers
        base_rods_per_layer = params.num_rods // params.num_layers
        extra_rods = params.num_rods % params.num_layers

        # Phase 3-4: Generate rods for each layer
        all_rods: list[Rod] = []

        for layer_num in range(1, params.num_layers + 1):
            # Check cancellation
            if self.is_cancelled():
                error_msg = "Generation cancelled"
                self.generation_failed.emit(error_msg)
                raise RuntimeError(error_msg)

            # Calculate target rods for this layer
            # Extra rods go to layers 1, 2, 3, ... sequentially
            target_rods = base_rods_per_layer + (1 if layer_num <= extra_rods else 0)

            direction = layer_directions[layer_num]

            # Generate rods for this layer
            layer_rods = self._generate_layer_rods(
                layer_num=layer_num,
                direction_deg=direction,
                target_rods=target_rods,
                frame=frame,
                anchor_points=anchor_points,
                weight_kg_m=params.infill_weight_per_meter_kg_m,
            )

            all_rods.extend(layer_rods)

            # Emit progress update
            elapsed = time.time() - start_time
            progress = GenerationProgress(iteration=layer_num, elapsed_sec=elapsed)
            self.progress_updated.emit(progress)

        # Verify rod count matches requested (Requirements 3.5, 5.5 - fail-fast)
        if len(all_rods) < params.num_rods:
            error_msg = (
                f"Failed to generate requested number of rods. "
                f"Generated: {len(all_rods)}, requested: {params.num_rods}. "
                f"Frame may be too small or min_anchor_distance_cm too large."
            )
            logger.error(error_msg)
            self.generation_failed.emit(error_msg)
            raise RuntimeError(error_msg)

        # Calculate generation duration
        elapsed = time.time() - start_time

        # Create infill result (without fitness score initially)
        infill = RailingInfill(
            rods=all_rods,
            fitness_score=None,
            iteration_count=1,  # Deterministic: always 1 iteration
            duration_sec=elapsed,
            anchor_points=anchor_points,
            is_complete=True,
        )

        # Run evaluator and set fitness score (Requirements 7.2, 7.3)
        fitness_score = evaluator.evaluate(infill, frame)

        # Create final infill with fitness score
        final_infill = RailingInfill(
            rods=all_rods,
            fitness_score=fitness_score,
            iteration_count=1,
            duration_sec=elapsed,
            anchor_points=anchor_points,
            is_complete=True,
        )

        logger.info(
            f"Generation complete: {len(all_rods)} rods generated in {elapsed:.3f}s, "
            f"fitness_score={fitness_score:.3f}"
        )

        # Emit signals (Requirements 9.3)
        self.best_result_updated.emit(final_infill)
        self.generation_completed.emit(final_infill)

        return final_infill

    def _generate_anchor_grid(
        self, frame: RailingFrame, params: UniformDirectionalGeneratorParameters
    ) -> list[AnchorPoint]:
        """
        Generate a grid of evenly spaced anchor points along the frame boundary.

        Creates as many anchor points as the minimum distance constraint allows
        along the entire frame boundary. All anchors start as "free" (not assigned
        to any rod).

        Algorithm:
        1. Calculate total frame perimeter
        2. Calculate spacing based on min_anchor_distance_cm
        3. Place anchors at regular intervals along frame boundary using Shapely's interpolate()
        4. Check and remove anchors that are too close at corners (Euclidean distance)
        5. All anchors start as "free" (not assigned to any rod)

        Note: The minimum distance constraint is enforced as Euclidean distance,
        not arc distance along the boundary. This means anchors near corners may
        be filtered out if they are too close to adjacent anchors.

        Args:
            frame: The railing frame defining the boundary
            params: Generation parameters containing min_anchor_distance_cm

        Returns:
            List of AnchorPoint objects, all marked as free (used=False)
        """
        boundary = frame.boundary
        perimeter = boundary.exterior.length
        min_distance = params.min_anchor_distance_cm

        # Calculate number of anchors based on minimum distance constraint
        # Use the minimum distance as the spacing along the boundary
        num_anchors = max(int(perimeter / min_distance), 2)
        spacing = perimeter / num_anchors

        logger.info(
            f"Generating anchor grid: perimeter={perimeter:.1f}cm, "
            f"min_distance={min_distance:.2f}cm, num_anchors={num_anchors}, spacing={spacing:.2f}cm"
        )

        # Generate anchor points at regular intervals
        candidate_points: list[Point] = []

        for i in range(num_anchors):
            distance_along_boundary = i * spacing
            point = boundary.exterior.interpolate(distance_along_boundary)
            candidate_points.append(Point(point.x, point.y))

        # Filter out anchors that are too close to their neighbors (Euclidean distance)
        # This handles corners where arc distance > Euclidean distance
        # Only check consecutive pairs and first/last pair (O(n) complexity)
        selected_points: list[Point] = []

        for i, point in enumerate(candidate_points):
            # Check distance to previous selected point
            if selected_points:
                prev_point = selected_points[-1]
                if point.distance(prev_point) < min_distance:
                    # Skip this point - too close to previous
                    continue

            selected_points.append(point)

        # Check if last point is too close to first (closed boundary)
        if len(selected_points) >= 2:
            first_point = selected_points[0]
            last_point = selected_points[-1]
            if first_point.distance(last_point) < min_distance:
                # Remove the last point if it's too close to the first
                selected_points.pop()

        # Create AnchorPoint objects from selected points
        anchor_points: list[AnchorPoint] = []

        for point in selected_points:
            # Determine which frame segment this anchor is on
            frame_segment_index, is_vertical, frame_segment_angle_deg = (
                self._find_frame_segment_for_point(frame, point)
            )

            anchor = AnchorPoint(
                position=point,
                frame_segment_index=frame_segment_index,
                is_vertical_segment=is_vertical,
                frame_segment_angle_deg=frame_segment_angle_deg,
                layer=None,  # Will be assigned later
                used=False,  # All anchors start as free
            )
            anchor_points.append(anchor)

        logger.info(
            f"Generated {len(anchor_points)} anchor points (filtered from {num_anchors} candidates)"
        )

        return anchor_points

    def _find_frame_segment_for_point(
        self, frame: RailingFrame, point: Point
    ) -> tuple[int, bool, float]:
        """
        Find which frame segment a point lies on.

        Args:
            frame: The railing frame
            point: The point to locate

        Returns:
            Tuple of (segment_index, is_vertical, frame_segment_angle_deg)
        """
        min_distance = float("inf")
        closest_segment_index = 0
        closest_is_vertical = False
        closest_angle_deg = 0.0

        for idx, rod in enumerate(frame.rods):
            distance = rod.geometry.distance(point)
            if distance < min_distance:
                min_distance = distance
                closest_segment_index = idx
                closest_is_vertical = self._is_vertical_segment(rod)
                closest_angle_deg = rod.angle_from_vertical_deg

        return closest_segment_index, closest_is_vertical, closest_angle_deg

    def _is_vertical_segment(self, rod: Rod) -> bool:
        """
        Classify a rod as vertical or not.

        A rod is considered vertical if its horizontal displacement (dx)
        is very small relative to its vertical displacement (dy).

        Args:
            rod: The rod to classify

        Returns:
            True if vertical, False otherwise
        """
        coords = list(rod.geometry.coords)
        dx = abs(coords[1][0] - coords[0][0])
        dy = abs(coords[1][1] - coords[0][1])

        # Consider vertical if dx is very small relative to dy
        # Use threshold of 0.1 (10% of dy)
        if dy > 0 and dx / dy < 0.1:
            return True
        return False

    def _calculate_layer_directions(
        self, params: UniformDirectionalGeneratorParameters
    ) -> dict[int, float]:
        """
        Calculate the main direction angle for each layer.

        For a single layer, uses the midpoint of the direction range.
        For multiple layers, distributes directions evenly across the range
        using linear interpolation.

        Formula for layer index i (0-based) with L layers:
        - If L == 1: direction = (min_deg + max_deg) / 2
        - If L > 1: direction = min_deg + (i / (L - 1)) * (max_deg - min_deg)

        Args:
            params: Generation parameters containing direction range and num_layers

        Returns:
            Dictionary mapping layer number (1-based) to direction angle in degrees
        """
        num_layers = params.num_layers
        min_deg = params.main_direction_range_min_deg
        max_deg = params.main_direction_range_max_deg

        layer_directions: dict[int, float] = {}

        if num_layers == 1:
            # Single layer: use midpoint of direction range
            midpoint = (min_deg + max_deg) / 2.0
            layer_directions[1] = midpoint
            logger.debug(f"Single layer direction: {midpoint:.2f}°")
        else:
            # Multiple layers: linear interpolation across the range
            for i in range(num_layers):
                # t is the interpolation factor (0.0 to 1.0)
                t = i / (num_layers - 1)
                direction = min_deg + t * (max_deg - min_deg)
                # Layer numbers are 1-based
                layer_directions[i + 1] = direction
                logger.debug(f"Layer {i + 1} direction: {direction:.2f}° (t={t:.3f})")

        return layer_directions

    def _calculate_polygon_extent(
        self,
        polygon: Polygon,
        perpendicular_direction: tuple[float, float],
    ) -> tuple[float, float]:
        """
        Calculate the extent of a polygon when projected onto a direction.

        Projects all polygon boundary vertices onto the perpendicular direction
        and returns the minimum and maximum projection values. This gives the
        actual extent of the polygon in that direction, which is more accurate
        than using the bounding box for non-rectangular shapes.

        Algorithm:
        1. Extract all vertices from the polygon exterior
        2. Project each vertex onto the perpendicular direction using dot product
        3. Find and return the minimum and maximum projection values

        Time complexity: O(n) where n is the number of boundary vertices.

        Args:
            polygon: The polygon to analyze (Shapely Polygon)
            perpendicular_direction: Unit vector (dx, dy) for the projection direction

        Returns:
            Tuple of (min_projection, max_projection) values

        Requirements: 1.1, 1.2, 3.1
        """
        perp_dx, perp_dy = perpendicular_direction

        # Get all vertices from the polygon exterior (excluding the closing vertex)
        # The exterior.coords includes the closing vertex which duplicates the first
        coords = list(polygon.exterior.coords)[:-1]

        # Project each vertex onto the perpendicular direction
        projections = [vx * perp_dx + vy * perp_dy for vx, vy in coords]

        # Return min and max projections
        return (min(projections), max(projections))

    def _calculate_valid_line_range(
        self,
        polygon: Polygon,
        line_direction: tuple[float, float],
        perpendicular_direction: tuple[float, float],
    ) -> tuple[float, float]:
        """
        Calculate the valid range where lines intersect the polygon at two points.

        For non-rectangular polygons, the polygon extent includes corners where
        lines only touch at one point. This method finds the overlap region
        between opposite edges where lines will produce valid two-point intersections.

        Algorithm:
        1. Find edges that are roughly perpendicular to the line direction (these are
           the edges that lines will intersect)
        2. Classify these edges as "positive" or "negative" based on their normal direction
        3. Find the overlap region between positive and negative edges
        4. Return the valid range where both types of edges exist

        For vertical lines in a parallelogram:
        - Top and bottom edges are perpendicular to vertical lines
        - The valid range is where top and bottom edges overlap horizontally

        Args:
            polygon: The polygon to analyze (Shapely Polygon)
            line_direction: Unit vector (dx, dy) for the line direction
            perpendicular_direction: Unit vector (dx, dy) for the perpendicular direction

        Returns:
            Tuple of (valid_min, valid_max) projection values where lines are valid

        Requirements: 1.3, 1.4, 1.5, 2.1
        """
        import math

        perp_dx, perp_dy = perpendicular_direction
        line_dx, line_dy = line_direction

        # Get all vertices from the polygon exterior (excluding the closing vertex)
        coords = list(polygon.exterior.coords)[:-1]
        n = len(coords)

        # Track projection ranges for edges that lines will intersect
        # "positive" edges have normals pointing in positive line direction (e.g., top edge)
        # "negative" edges have normals pointing in negative line direction (e.g., bottom edge)
        positive_edge_ranges: list[tuple[float, float]] = []
        negative_edge_ranges: list[tuple[float, float]] = []

        for i in range(n):
            # Get edge vertices
            v1 = coords[i]
            v2 = coords[(i + 1) % n]

            # Calculate edge direction
            edge_dx = v2[0] - v1[0]
            edge_dy = v2[1] - v1[1]
            edge_length = math.sqrt(edge_dx**2 + edge_dy**2)

            if edge_length < 1e-9:
                continue  # Skip degenerate edges

            # Normalize edge direction
            edge_dx /= edge_length
            edge_dy /= edge_length

            # Calculate edge normal (perpendicular to edge, pointing outward for CCW polygon)
            # For CCW polygon, outward normal is (-edge_dy, edge_dx)
            normal_dx = -edge_dy
            normal_dy = edge_dx

            # Check if edge is roughly perpendicular to line direction
            # by checking if the edge normal is roughly parallel to line direction
            # This means the edge is roughly horizontal for vertical lines
            normal_dot_line = normal_dx * line_dx + normal_dy * line_dy
            abs_normal_dot_line = abs(normal_dot_line)

            # Only include edges that are strongly perpendicular to line direction
            # (i.e., their normal is strongly aligned with line direction)
            if abs_normal_dot_line > 0.9:  # Edge is roughly perpendicular to line direction
                # Calculate projection range of this edge onto perpendicular direction
                proj1 = v1[0] * perp_dx + v1[1] * perp_dy
                proj2 = v2[0] * perp_dx + v2[1] * perp_dy
                edge_min = min(proj1, proj2)
                edge_max = max(proj1, proj2)

                if normal_dot_line > 0:
                    positive_edge_ranges.append((edge_min, edge_max))
                else:
                    negative_edge_ranges.append((edge_min, edge_max))

        # If we don't have edges in both directions, fall back to polygon extent
        if not positive_edge_ranges or not negative_edge_ranges:
            return self._calculate_polygon_extent(polygon, perpendicular_direction)

        # Find the overlap region between positive and negative edges
        # For each positive edge, find where it overlaps with negative edges
        # The valid range is the intersection of all these overlaps

        # Combine all positive edges into one range (union)
        pos_min = min(edge_min for edge_min, _ in positive_edge_ranges)
        pos_max = max(edge_max for _, edge_max in positive_edge_ranges)

        # Combine all negative edges into one range (union)
        neg_min = min(edge_min for edge_min, _ in negative_edge_ranges)
        neg_max = max(edge_max for _, edge_max in negative_edge_ranges)

        # The valid range is the intersection of positive and negative ranges
        valid_min = max(pos_min, neg_min)
        valid_max = min(pos_max, neg_max)

        # If there's no overlap, fall back to polygon extent
        if valid_min >= valid_max:
            return self._calculate_polygon_extent(polygon, perpendicular_direction)

        return (valid_min, valid_max)

    def _generate_line_pattern(
        self,
        frame: RailingFrame,
        direction_deg: float,
        num_lines: int,
    ) -> list[LineString]:
        """
        Generate a pattern of parallel lines across the frame at a given direction angle.

        Creates evenly spaced parallel lines that span the valid region of the frame polygon.
        The lines are oriented at the specified direction angle from vertical.

        Algorithm:
        1. Calculate the perpendicular direction for line spacing
        2. Calculate the valid line range where lines intersect at two points
        3. Generate parallel lines evenly spaced across this valid range
        4. All generated lines will produce valid two-point intersections

        This method uses the valid line range calculation to ensure even distribution
        across non-rectangular shapes like parallelograms, avoiding corners where
        lines would only touch at one point.

        Args:
            frame: The railing frame defining the boundary
            direction_deg: Direction angle in degrees (0° = vertical, positive = clockwise)
            num_lines: Number of parallel lines to generate

        Returns:
            List of LineString objects representing the parallel lines

        Requirements: 1.3, 1.4, 1.5, 2.1, 2.2, 2.3
        """
        import math

        if num_lines <= 0:
            return []

        # Get frame bounding box for calculating line length
        minx, miny, maxx, maxy = frame.boundary.bounds
        width = maxx - minx
        height = maxy - miny

        # Convert direction angle to radians
        # 0° = vertical (pointing up), positive = clockwise
        angle_rad = math.radians(direction_deg)

        # Direction vector for the lines (along the line direction)
        # For 0° (vertical): dx=0, dy=1 (pointing up)
        # For 90° (horizontal): dx=1, dy=0 (pointing right)
        line_dx = math.sin(angle_rad)
        line_dy = math.cos(angle_rad)

        # Perpendicular direction for spacing (90° counterclockwise from line direction)
        perp_dx = -line_dy  # = -cos(angle)
        perp_dy = line_dx  # = sin(angle)

        # Calculate the diagonal of the bounding box to ensure lines span the entire frame
        diagonal = math.sqrt(width**2 + height**2)

        # Line length should be at least the diagonal to ensure full coverage
        line_half_length = diagonal

        # Calculate the valid line range where lines intersect at two points
        # This is the key fix: use valid range instead of polygon extent
        line_direction = (line_dx, line_dy)
        perpendicular_direction = (perp_dx, perp_dy)
        min_proj, max_proj = self._calculate_valid_line_range(
            frame.boundary, line_direction, perpendicular_direction
        )

        # Calculate the effective range (valid line range)
        effective_range = max_proj - min_proj

        # Use polygon centroid as reference point for calculating line positions
        centroid = frame.boundary.centroid
        centroid_proj = centroid.x * perp_dx + centroid.y * perp_dy

        # Generate lines
        lines: list[LineString] = []

        if num_lines == 1:
            # Single line at the center of the effective range
            center_offset = (min_proj + max_proj) / 2.0

            # Calculate the point at the center offset
            offset_diff = center_offset - centroid_proj
            line_center_x = centroid.x + offset_diff * perp_dx
            line_center_y = centroid.y + offset_diff * perp_dy

            # Calculate line endpoints
            start_x = line_center_x - line_dx * line_half_length
            start_y = line_center_y - line_dy * line_half_length
            end_x = line_center_x + line_dx * line_half_length
            end_y = line_center_y + line_dy * line_half_length
            lines.append(LineString([(start_x, start_y), (end_x, end_y)]))
        else:
            # Multiple lines evenly spaced from min_proj to max_proj
            spacing = effective_range / (num_lines - 1)

            for i in range(num_lines):
                # Calculate offset in perpendicular direction
                # Goes from min_proj to max_proj (valid line range)
                offset = min_proj + i * spacing

                # Calculate the point at this offset
                offset_diff = offset - centroid_proj
                line_center_x = centroid.x + offset_diff * perp_dx
                line_center_y = centroid.y + offset_diff * perp_dy

                # Calculate line endpoints
                start_x = line_center_x - line_dx * line_half_length
                start_y = line_center_y - line_dy * line_half_length
                end_x = line_center_x + line_dx * line_half_length
                end_y = line_center_y + line_dy * line_half_length

                lines.append(LineString([(start_x, start_y), (end_x, end_y)]))

        logger.debug(
            f"Generated {len(lines)} parallel lines at {direction_deg:.1f}° "
            f"with spacing {effective_range / max(num_lines - 1, 1):.2f}cm "
            f"across polygon extent [{min_proj:.2f}, {max_proj:.2f}]"
        )

        return lines

    def _find_boundary_intersections(
        self,
        lines: list[LineString],
        frame: RailingFrame,
    ) -> list[tuple[Point, Point] | None]:
        """
        Find intersections of each line with the frame boundary.

        For each line, finds where it intersects the frame boundary. A valid
        intersection produces exactly two points (entry and exit). Lines that
        don't intersect or have complex intersections return None.

        Args:
            lines: List of LineString objects to intersect with boundary
            frame: The railing frame defining the boundary

        Returns:
            List of tuples (point1, point2) for valid intersections, or None
            for lines that don't produce valid intersection pairs.

        Requirements: 6.3
        """
        results: list[tuple[Point, Point] | None] = []

        for line in lines:
            intersection = line.intersection(frame.boundary.exterior)

            if intersection.is_empty:
                # No intersection
                results.append(None)
                continue

            # Extract intersection points
            intersection_points: list[Point] = []

            if intersection.geom_type == "Point":
                # Single point intersection (tangent) - not useful for a rod
                results.append(None)
                continue
            elif intersection.geom_type == "MultiPoint":
                # Multiple points - extract all
                from shapely.geometry import MultiPoint as ShapelyMultiPoint

                if isinstance(intersection, ShapelyMultiPoint):
                    intersection_points = [Point(p.x, p.y) for p in intersection.geoms]
            elif intersection.geom_type == "LineString":
                # Line segment intersection (line lies on boundary) - use endpoints
                if isinstance(intersection, LineString):
                    coords = list(intersection.coords)
                    if len(coords) >= 2:
                        intersection_points = [
                            Point(coords[0][0], coords[0][1]),
                            Point(coords[-1][0], coords[-1][1]),
                        ]
            elif intersection.geom_type == "GeometryCollection":
                # Mixed geometry - extract all points
                from shapely.geometry import GeometryCollection, MultiPoint as ShapelyMultiPoint

                if isinstance(intersection, GeometryCollection):
                    for geom in intersection.geoms:
                        if geom.geom_type == "Point":
                            intersection_points.append(Point(geom.x, geom.y))
                        elif geom.geom_type == "MultiPoint" and isinstance(geom, ShapelyMultiPoint):
                            intersection_points.extend([Point(p.x, p.y) for p in geom.geoms])

            # We need exactly 2 intersection points for a valid rod
            if len(intersection_points) == 2:
                results.append((intersection_points[0], intersection_points[1]))
            elif len(intersection_points) > 2:
                # More than 2 intersections - take the two furthest apart
                # This handles cases where the line crosses corners
                max_distance = 0.0
                best_pair: tuple[Point, Point] | None = None
                for i, p1 in enumerate(intersection_points):
                    for p2 in intersection_points[i + 1 :]:
                        dist = p1.distance(p2)
                        if dist > max_distance:
                            max_distance = dist
                            best_pair = (p1, p2)
                results.append(best_pair)
            else:
                # Less than 2 points - invalid
                results.append(None)

        logger.debug(
            f"Found {sum(1 for r in results if r is not None)} valid intersections "
            f"out of {len(lines)} lines"
        )

        return results

    def _snap_to_nearest_anchor(
        self,
        point: Point,
        free_anchors: list[AnchorPoint],
        max_snap_distance_cm: float | None = None,
    ) -> AnchorPoint | None:
        """
        Find the nearest free anchor to a given point.

        Searches through the list of free (unused) anchors and returns the
        closest one to the given point. Optionally limits the search to
        anchors within a maximum distance.

        Args:
            point: The point to find the nearest anchor to
            free_anchors: List of free (unused) anchor points to search
            max_snap_distance_cm: Maximum distance to consider (None = no limit)

        Returns:
            The nearest free AnchorPoint, or None if no suitable anchor found

        Requirements: 3.2, 6.4
        """
        if not free_anchors:
            return None

        nearest_anchor: AnchorPoint | None = None
        min_distance = float("inf")

        for anchor in free_anchors:
            if anchor.used:
                # Skip already used anchors
                continue

            distance = point.distance(anchor.position)

            # Check max distance constraint if specified
            if max_snap_distance_cm is not None and distance > max_snap_distance_cm:
                continue

            if distance < min_distance:
                min_distance = distance
                nearest_anchor = anchor

        if nearest_anchor is not None:
            logger.debug(
                f"Snapped point ({point.x:.1f}, {point.y:.1f}) to anchor at "
                f"({nearest_anchor.position.x:.1f}, {nearest_anchor.position.y:.1f}), "
                f"distance={min_distance:.2f}cm"
            )

        return nearest_anchor

    def _calculate_cut_angles(
        self,
        rod_angle_deg: float,
        start_anchor: AnchorPoint,
        end_anchor: AnchorPoint,
    ) -> tuple[float, float]:
        """
        Calculate start and end cut angles for a rod based on frame segment angles.

        The cut angle is the angle between the rod and the frame segment it attaches to.
        This is calculated as the difference between the rod angle and the frame segment angle.

        Args:
            rod_angle_deg: Angle of the rod from vertical in degrees
            start_anchor: Starting anchor point with frame segment angle
            end_anchor: Ending anchor point with frame segment angle

        Returns:
            Tuple of (start_cut_angle_deg, end_cut_angle_deg)
        """
        # Calculate cut angles as the difference between rod angle and frame segment angle
        start_cut_angle = rod_angle_deg - start_anchor.frame_segment_angle_deg
        end_cut_angle = rod_angle_deg - end_anchor.frame_segment_angle_deg

        # Normalize angles to [-90, 90] range by wrapping around
        def normalize_cut_angle(angle: float) -> float:
            # Wrap angle to [-180, 180] first
            while angle > 180:
                angle -= 360
            while angle < -180:
                angle += 360

            # If angle is outside [-90, 90], flip it
            if angle > 90:
                angle = 180 - angle
            elif angle < -90:
                angle = -180 - angle

            return angle

        start_cut_angle = normalize_cut_angle(start_cut_angle)
        end_cut_angle = normalize_cut_angle(end_cut_angle)

        return start_cut_angle, end_cut_angle

    def _rotate_point(
        self, x: float, y: float, angle_rad: float, cx: float, cy: float
    ) -> tuple[float, float]:
        """
        Rotate a point around a center point.

        Args:
            x, y: Point coordinates to rotate
            angle_rad: Rotation angle in radians (positive = counterclockwise)
            cx, cy: Center of rotation

        Returns:
            Tuple of (rotated_x, rotated_y)
        """
        import math

        # Translate to origin
        dx = x - cx
        dy = y - cy

        # Rotate
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a

        # Translate back
        return (rx + cx, ry + cy)

    def _generate_layer_rods(
        self,
        layer_num: int,
        direction_deg: float,
        target_rods: int,
        frame: RailingFrame,
        anchor_points: list[AnchorPoint],
        weight_kg_m: float,
    ) -> list[Rod]:
        """
        Generate rods for a single layer using rotation-based uniform distribution.

        Algorithm (rotation-based approach for correct uniform distribution):
        1. Rotate frame and anchor points so the layer direction becomes vertical
        2. In rotated space, use the frame bounding box width as the full extent
        3. Calculate rod x-positions evenly spaced across the full extent
        4. For each x-position, find the highest-y and lowest-y free anchors nearby
           (these are guaranteed to be on opposite edges)
        5. Create rods connecting these anchor pairs in original geometry

        Args:
            layer_num: Layer number (1-based)
            direction_deg: Direction angle for this layer in degrees
            target_rods: Target number of rods to generate for this layer
            frame: The railing frame defining the boundary
            anchor_points: List of all anchor points (some may already be used)
            weight_kg_m: Weight per meter for the rods

        Returns:
            List of Rod objects generated for this layer

        Requirements: 1.4, 5.4, 6.4
        """
        import math

        logger.info(
            f"Generating layer {layer_num}: target={target_rods} rods, "
            f"direction={direction_deg:.1f}°"
        )

        if target_rods <= 0:
            return []

        # Get frame centroid as rotation center
        centroid = frame.boundary.centroid
        cx, cy = centroid.x, centroid.y

        # Calculate rotation angle to make layer direction vertical
        # direction_deg: 0° = vertical, positive = clockwise
        # We need to rotate by -direction_deg to make it vertical
        rotation_angle_rad = math.radians(-direction_deg)

        # Rotate all anchor points and store with their original indices
        # Structure: list of (rotated_x, rotated_y, original_index, anchor)
        rotated_anchors: list[tuple[float, float, int, AnchorPoint]] = []
        for idx, anchor in enumerate(anchor_points):
            rx, ry = self._rotate_point(
                anchor.position.x, anchor.position.y, rotation_angle_rad, cx, cy
            )
            rotated_anchors.append((rx, ry, idx, anchor))

        # Rotate frame boundary to get bounding box in rotated space
        rotated_coords = [
            self._rotate_point(x, y, rotation_angle_rad, cx, cy)
            for x, y in frame.boundary.exterior.coords
        ]
        rotated_xs = [x for x, y in rotated_coords]
        min_x_rotated = min(rotated_xs)
        max_x_rotated = max(rotated_xs)

        # Use the FRAME bounding box as the full extent for even distribution
        valid_x_min = min_x_rotated
        valid_x_max = max_x_rotated
        valid_extent = valid_x_max - valid_x_min

        logger.debug(
            f"Layer {layer_num}: Rotated extent = {valid_extent:.2f}cm, "
            f"x range = [{valid_x_min:.2f}, {valid_x_max:.2f}]"
        )

        if valid_extent <= 0:
            logger.warning(f"Layer {layer_num}: No valid x-range for rod placement")
            return []

        # Filter to only unused anchors for rod creation
        free_rotated_anchors = [
            (rx, ry, idx, anchor) for rx, ry, idx, anchor in rotated_anchors if not anchor.used
        ]

        if len(free_rotated_anchors) < 2:
            logger.warning(f"Layer {layer_num}: Not enough free anchors")
            return []

        # Calculate rod x-positions: evenly distributed across the full extent
        rod_x_positions: list[float] = []

        if target_rods == 1:
            rod_x_positions = [(valid_x_min + valid_x_max) / 2.0]
        else:
            # Spacing between rods to fill the full extent
            spacing = valid_extent / (target_rods - 1)
            for i in range(target_rods):
                x_pos = valid_x_min + i * spacing
                rod_x_positions.append(x_pos)

        logger.debug(
            f"Layer {layer_num}: Rod x-positions (rotated space): "
            f"{[f'{x:.2f}' for x in rod_x_positions]}"
        )

        # For each rod position, find the highest-y and lowest-y anchors nearby
        # This guarantees we connect opposite edges regardless of frame shape
        layer_rods: list[Rod] = []

        for rod_x in rod_x_positions:
            # Find anchor pair: highest-y and lowest-y near this x-position
            anchor_pair = self._find_opposite_anchors_at_x(
                rod_x, free_rotated_anchors, rotated_anchors
            )
            if anchor_pair is None:
                logger.debug(f"Layer {layer_num}: No anchor pair found for x={rod_x:.2f}")
                continue

            high_anchor, low_anchor = anchor_pair

            # Mark anchors as used
            high_anchor.used = True
            low_anchor.used = True

            # Update free anchors list
            free_rotated_anchors = [
                (rx, ry, idx, a) for rx, ry, idx, a in free_rotated_anchors if not a.used
            ]

            # Create rod using original (non-rotated) anchor positions
            rod_geometry = LineString(
                [high_anchor.position.coords[0], low_anchor.position.coords[0]]
            )

            # Create temporary rod to get its angle
            temp_rod = Rod(
                geometry=rod_geometry,
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=weight_kg_m,
                layer=layer_num,
            )

            # Calculate cut angles
            start_cut_angle, end_cut_angle = self._calculate_cut_angles(
                rod_angle_deg=temp_rod.angle_from_vertical_deg,
                start_anchor=high_anchor,
                end_anchor=low_anchor,
            )

            # Create final rod
            rod = Rod(
                geometry=rod_geometry,
                start_cut_angle_deg=start_cut_angle,
                end_cut_angle_deg=end_cut_angle,
                weight_kg_m=weight_kg_m,
                layer=layer_num,
            )

            # Check for crossings with existing rods in this layer
            if self._rod_crosses_existing_rods(rod, layer_rods):
                # Restore anchors
                high_anchor.used = False
                low_anchor.used = False
                free_rotated_anchors = [
                    (rx, ry, idx, a) for rx, ry, idx, a in rotated_anchors if not a.used
                ]
                logger.debug(f"Layer {layer_num}: Rod would cross existing rods")
                continue

            # Assign layer to anchors
            high_anchor.layer = layer_num
            low_anchor.layer = layer_num

            layer_rods.append(rod)

            logger.debug(
                f"Layer {layer_num}: Created rod {len(layer_rods)} "
                f"from ({high_anchor.position.x:.1f}, {high_anchor.position.y:.1f}) "
                f"to ({low_anchor.position.x:.1f}, {low_anchor.position.y:.1f})"
            )

        logger.info(f"Layer {layer_num} complete: {len(layer_rods)}/{target_rods} rods generated")

        return layer_rods

    def _find_opposite_anchors_at_x(
        self,
        target_x: float,
        free_rotated_anchors: list[tuple[float, float, int, AnchorPoint]],
        all_rotated_anchors: list[tuple[float, float, int, AnchorPoint]],
    ) -> tuple[AnchorPoint, AnchorPoint] | None:
        """
        Find a pair of anchors on opposite edges near a target x-coordinate.

        For each x-position, finds the free anchor with highest y and the free anchor
        with lowest y. These are guaranteed to be on opposite edges of the frame.

        Args:
            target_x: Target x-coordinate in rotated space
            free_rotated_anchors: List of unused (rotated_x, rotated_y, idx, anchor) tuples
            all_rotated_anchors: All anchors for reference

        Returns:
            Tuple of (high_y_anchor, low_y_anchor) or None if not found
        """
        if len(free_rotated_anchors) < 2:
            return None

        # Find anchors closest to target_x, then pick highest and lowest y among them
        # Use a tolerance based on anchor spacing
        x_coords = [rx for rx, ry, idx, a in free_rotated_anchors]
        if not x_coords:
            return None

        # Calculate a reasonable x-tolerance (half the average spacing between anchors)
        x_coords_sorted = sorted(x_coords)
        if len(x_coords_sorted) > 1:
            avg_spacing = (x_coords_sorted[-1] - x_coords_sorted[0]) / (len(x_coords_sorted) - 1)
            x_tolerance = max(avg_spacing * 1.5, 10.0)  # At least 10cm tolerance
        else:
            x_tolerance = 50.0  # Default tolerance

        # Find all anchors within x-tolerance of target_x
        nearby_anchors = [
            (rx, ry, idx, anchor)
            for rx, ry, idx, anchor in free_rotated_anchors
            if abs(rx - target_x) <= x_tolerance
        ]

        if len(nearby_anchors) < 2:
            # Expand search to find at least 2 anchors
            # Sort all free anchors by distance to target_x and take closest ones
            sorted_by_x_dist = sorted(free_rotated_anchors, key=lambda a: abs(a[0] - target_x))
            nearby_anchors = sorted_by_x_dist[: min(10, len(sorted_by_x_dist))]

        if len(nearby_anchors) < 2:
            return None

        # Find the anchor with highest y and lowest y among nearby anchors
        high_y_data = max(nearby_anchors, key=lambda a: a[1])
        low_y_data = min(nearby_anchors, key=lambda a: a[1])

        # Make sure they're different anchors
        if high_y_data[3] is low_y_data[3]:
            return None

        return (high_y_data[3], low_y_data[3])

    def _rod_crosses_existing_rods(self, new_rod: Rod, existing_rods: list[Rod]) -> bool:
        """
        Check if a new rod crosses any existing rods.

        A crossing is defined as an intersection at a point that is not at
        an endpoint of either rod (i.e., a true crossing in the middle).

        Args:
            new_rod: The rod to check
            existing_rods: List of existing rods to check against

        Returns:
            True if the new rod crosses any existing rod, False otherwise

        Requirements: 6.1
        """
        for existing_rod in existing_rods:
            intersection = new_rod.geometry.intersection(existing_rod.geometry)

            # If intersection is empty, no crossing
            if intersection.is_empty:
                continue

            # If intersection is a point, check if it's at an endpoint
            if intersection.geom_type == "Point":
                # Check if intersection is at an endpoint of either rod
                is_at_endpoint = (
                    intersection.equals(new_rod.start_point)
                    or intersection.equals(new_rod.end_point)
                    or intersection.equals(existing_rod.start_point)
                    or intersection.equals(existing_rod.end_point)
                )

                if not is_at_endpoint:
                    # This is a true crossing in the middle of both rods
                    logger.debug(
                        f"Rod crossing detected at {intersection}: "
                        f"new rod from {new_rod.start_point} to {new_rod.end_point}, "
                        f"existing rod from {existing_rod.start_point} to {existing_rod.end_point}"
                    )
                    return True

            # If intersection is a line segment, the rods overlap (also a crossing)
            elif intersection.geom_type == "LineString":
                logger.debug(
                    f"Rod overlap detected: "
                    f"new rod from {new_rod.start_point} to {new_rod.end_point}, "
                    f"existing rod from {existing_rod.start_point} to {existing_rod.end_point}"
                )
                return True

        return False
