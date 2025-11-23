"""Random infill generator v2 implementation with layered directional approach."""

import logging
import random
from typing import TYPE_CHECKING

from railing_generator.domain.anchor_point import AnchorPoint
from railing_generator.domain.evaluators.evaluator import Evaluator
from railing_generator.domain.evaluators.evaluator_factory import EvaluatorFactory
from railing_generator.domain.infill_generators.generation_statistics import (
    GenerationStatistics,
)
from railing_generator.domain.infill_generators.generator import Generator
from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorParameters,
)
from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
    RandomGeneratorParametersV2,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod

if TYPE_CHECKING:
    from shapely.geometry import LineString

logger = logging.getLogger(__name__)


class RandomGeneratorV2(Generator):
    """
    Enhanced random infill generator with layered directional approach.

    Key features:
    - Frame-segment-aware anchor point spacing
    - Pre-generated anchor points distributed to layers
    - Layer-specific main directions with controlled variation
    - Efficient rod generation via projection and nearest-anchor search
    - Requires an evaluator for fitness scoring (Pass-Through or Quality)
    """

    # Define the parameter type for this generator
    PARAMETER_TYPE = RandomGeneratorParametersV2

    def __init__(self) -> None:
        """Initialize the random generator v2."""
        super().__init__()
        self.statistics = GenerationStatistics()
        self.evaluator: Evaluator | None = None  # Will be set when generate() is called

    def get_statistics(self) -> GenerationStatistics:
        """
        Get the statistics from the last generation run.

        Returns:
            GenerationStatistics object with metrics from last generation
        """
        return self.statistics

    def generate(self, frame: RailingFrame, params: InfillGeneratorParameters) -> RailingInfill:
        """
        Generate random infill arrangement within the frame using v2 approach.

        Args:
            frame: The railing frame defining the boundary
            params: RandomGeneratorParametersV2 for generation

        Returns:
            RailingInfill containing the generated rods

        Raises:
            ValueError: If parameters are not RandomGeneratorParametersV2
            RuntimeError: If generation fails
        """
        # Validate and narrow parameter type (runtime check for type safety)
        if not isinstance(params, RandomGeneratorParametersV2):
            raise ValueError(
                f"RandomGeneratorV2 requires RandomGeneratorParametersV2, "
                f"got {type(params).__name__}"
            )

        # Generator creates its own evaluator from nested parameters
        self.evaluator = EvaluatorFactory.create_evaluator(params.evaluator)

        # Reset cancellation flag
        self.reset_cancellation()

        # Initialize statistics for this generation run
        self.statistics = GenerationStatistics(rods_requested=params.num_rods)

        # Start generation
        import time

        start_time = time.time()
        all_rods: list[Rod] = []
        total_iterations = 0

        try:
            # Phase 1: Generate anchor points
            anchor_points_by_segment = self._generate_anchor_points_by_frame_segment(frame, params)

            # Phase 2: Distribute anchors to layers
            anchors_by_layer = self._distribute_anchors_to_layers(
                anchor_points_by_segment, params.num_layers
            )

            # Collect all anchor points for visualization
            anchor_points_for_infill: list[AnchorPoint] = []
            for anchors in anchors_by_layer.values():
                anchor_points_for_infill.extend(anchors)

            # Phase 3: Calculate layer main directions
            layer_main_directions = self._calculate_layer_main_directions(
                params.num_layers,
                params.main_direction_range_min_deg,
                params.main_direction_range_max_deg,
            )

            # Phase 4: Generate rods layer by layer
            for layer_num in range(1, params.num_layers + 1):
                # Check cancellation
                if self.is_cancelled():
                    elapsed = time.time() - start_time
                    infill = RailingInfill(
                        rods=all_rods,
                        fitness_score=None,
                        iteration_count=total_iterations,
                        duration_sec=elapsed,
                        anchor_points=anchor_points_for_infill,
                    )
                    self.statistics.rods_created = len(all_rods)
                    self.statistics.iterations_used = total_iterations
                    self.statistics.duration_sec = elapsed
                    logger.info(
                        f"Generation cancelled with {len(all_rods)} rods:\n{self.statistics}"
                    )
                    self.generation_completed.emit(infill)
                    return infill

                # Check duration limit
                elapsed = time.time() - start_time
                if elapsed > params.max_duration_sec:
                    infill = RailingInfill(
                        rods=all_rods,
                        fitness_score=None,
                        iteration_count=total_iterations,
                        duration_sec=elapsed,
                        anchor_points=anchor_points_for_infill,
                    )
                    self.statistics.rods_created = len(all_rods)
                    self.statistics.iterations_used = total_iterations
                    self.statistics.duration_sec = elapsed
                    logger.info(f"Generation timeout with {len(all_rods)} rods:\n{self.statistics}")
                    self.generation_completed.emit(infill)
                    return infill

                layer_rods, layer_iterations = self._generate_layer_rods(
                    layer_num=layer_num,
                    available_anchors=anchors_by_layer[layer_num],
                    main_direction=layer_main_directions[layer_num],
                    frame=frame,
                    params=params,
                    existing_rods=all_rods,
                )

                all_rods.extend(layer_rods)
                total_iterations += layer_iterations

                # Emit progress
                self.progress_updated.emit(
                    {
                        "iteration": total_iterations,
                        "best_fitness": None,
                        "elapsed_sec": elapsed,
                    }
                )

                # Check iteration limit
                if total_iterations >= params.max_iterations:
                    break

            # Create result
            elapsed = time.time() - start_time
            infill = RailingInfill(
                rods=all_rods,
                fitness_score=None,  # No fitness evaluation in v2
                iteration_count=total_iterations,
                duration_sec=elapsed,
                anchor_points=anchor_points_for_infill,
            )

            # Update statistics
            self.statistics.rods_created = len(all_rods)
            self.statistics.iterations_used = total_iterations
            self.statistics.duration_sec = elapsed

            # Log final statistics
            logger.info(f"Generation complete:\n{self.statistics}")

            # Emit signals
            self.best_result_updated.emit(infill)
            self.generation_completed.emit(infill)

            return infill

        except Exception as e:
            # Return partial results even on failure
            elapsed = time.time() - start_time
            if all_rods:
                infill = RailingInfill(
                    rods=all_rods,
                    fitness_score=None,
                    iteration_count=total_iterations,
                    duration_sec=elapsed,
                    anchor_points=anchor_points_for_infill
                    if "anchor_points_for_infill" in locals()
                    else None,
                )
                self.statistics.rods_created = len(all_rods)
                self.statistics.iterations_used = total_iterations
                self.statistics.duration_sec = elapsed
                error_msg = f"Generation failed with {len(all_rods)} partial rods: {str(e)}"
                logger.error(f"{error_msg}\n{self.statistics}")
                self.generation_completed.emit(infill)
                return infill

            error_msg = f"Generation failed: {str(e)}"
            logger.error(error_msg)
            self.generation_failed.emit(error_msg)
            raise RuntimeError(error_msg) from e

    def _classify_frame_segment(self, frame_rod: Rod) -> bool:
        """
        Classify frame segment as vertical or not.

        A frame rod is considered vertical if its horizontal displacement (dx)
        is very small relative to its vertical displacement (dy). Uses a threshold
        of 0.1 (10% of dy).

        Args:
            frame_rod: The frame rod to classify

        Returns:
            True if vertical, False if horizontal/sloped
        """
        coords = list(frame_rod.geometry.coords)
        dx = abs(coords[1][0] - coords[0][0])
        dy = abs(coords[1][1] - coords[0][1])

        # Consider vertical if dx is very small relative to dy
        # Use threshold of 0.1 (10% of dy)
        if dy > 0 and dx / dy < 0.1:
            return True
        return False

    def _generate_anchor_points_by_frame_segment(
        self, frame: RailingFrame, params: RandomGeneratorParametersV2
    ) -> dict[int, list[AnchorPoint]]:
        """
        Generate anchor points for each frame segment.

        Creates anchor points along the frame boundary with appropriate spacing
        based on frame segment orientation (vertical vs horizontal/sloped).

        Args:
            frame: The railing frame
            params: Generation parameters

        Returns:
            Dictionary mapping frame segment index to list of anchor points
        """
        logger.info("Starting anchor point generation")

        anchor_points_by_segment: dict[int, list[AnchorPoint]] = {}
        total_anchor_count = 0

        # Process each frame rod (segment)
        for segment_idx, frame_rod in enumerate(frame.rods):
            # Classify segment as vertical or other
            is_vertical = self._classify_frame_segment(frame_rod)

            # Select appropriate minimum distance
            min_distance = (
                params.min_anchor_distance_vertical_cm
                if is_vertical
                else params.min_anchor_distance_other_cm
            )

            # Generate anchor points along this segment
            segment_length = frame_rod.geometry.length
            num_anchors = max(int(segment_length / min_distance), 2)

            anchors = []
            for i in range(num_anchors):
                # Evenly distribute with small random offset
                base_position = (i / (num_anchors - 1)) * segment_length if num_anchors > 1 else 0
                offset = random.uniform(-min_distance * 0.2, min_distance * 0.2)
                position = max(0, min(segment_length, base_position + offset))

                # Get point at this position along the segment
                point = frame_rod.geometry.interpolate(position)

                anchor = AnchorPoint(
                    position=(point.x, point.y),
                    frame_segment_index=segment_idx,
                    is_vertical_segment=is_vertical,
                    layer=None,
                    used=False,
                )
                anchors.append(anchor)

            anchor_points_by_segment[segment_idx] = anchors
            total_anchor_count += len(anchors)

        logger.info(
            f"Generated {total_anchor_count} anchor points across "
            f"{len(anchor_points_by_segment)} frame segments (before cleanup)"
        )

        # Post-process: Remove anchors that are too close across segment boundaries
        anchor_points_by_segment = self._cleanup_boundary_anchors(
            anchor_points_by_segment, frame, params
        )

        # Recount after cleanup
        total_anchor_count = sum(len(anchors) for anchors in anchor_points_by_segment.values())
        logger.info(f"After cleanup: {total_anchor_count} anchor points")

        return anchor_points_by_segment

    def _cleanup_boundary_anchors(
        self,
        anchor_points_by_segment: dict[int, list[AnchorPoint]],
        frame: RailingFrame,
        params: RandomGeneratorParametersV2,
    ) -> dict[int, list[AnchorPoint]]:
        """
        Remove anchors that are too close across segment boundaries.

        Checks the distance between the last anchor of each segment and the first
        anchor of the next segment. If they're too close, removes the first anchor
        of the next segment.

        Args:
            anchor_points_by_segment: Dictionary mapping segment index to anchor points
            frame: The railing frame
            params: Generation parameters

        Returns:
            Cleaned up dictionary with boundary violations removed
        """
        import math

        cleaned_segments: dict[int, list[AnchorPoint]] = {}

        for segment_idx in range(len(frame.rods)):
            if segment_idx not in anchor_points_by_segment:
                continue

            anchors = list(anchor_points_by_segment[segment_idx])

            # Check distance to previous segment's last anchor
            if segment_idx > 0 and (segment_idx - 1) in cleaned_segments:
                prev_anchors = cleaned_segments[segment_idx - 1]
                if prev_anchors and anchors:
                    # Get last anchor of previous segment
                    last_prev = prev_anchors[-1]
                    # Get first anchor of current segment
                    first_curr = anchors[0]

                    # Calculate distance
                    dx = first_curr.position[0] - last_prev.position[0]
                    dy = first_curr.position[1] - last_prev.position[1]
                    distance = math.sqrt(dx * dx + dy * dy)

                    # Determine minimum distance based on segment types
                    # Use the more restrictive (smaller) of the two distances
                    min_dist_prev = (
                        params.min_anchor_distance_vertical_cm
                        if last_prev.is_vertical_segment
                        else params.min_anchor_distance_other_cm
                    )
                    min_dist_curr = (
                        params.min_anchor_distance_vertical_cm
                        if first_curr.is_vertical_segment
                        else params.min_anchor_distance_other_cm
                    )
                    min_distance = min(min_dist_prev, min_dist_curr)

                    # If too close, remove the first anchor of current segment
                    if distance < min_distance:
                        logger.debug(
                            f"Removing anchor at segment boundary {segment_idx - 1}->{segment_idx}: "
                            f"distance {distance:.1f}cm < {min_distance:.1f}cm"
                        )
                        anchors = anchors[1:]  # Remove first anchor

            cleaned_segments[segment_idx] = anchors

        return cleaned_segments

    def _distribute_anchors_to_layers(
        self, anchor_points_by_segment: dict[int, list[AnchorPoint]], num_layers: int
    ) -> dict[int, list[AnchorPoint]]:
        """
        Distribute anchor points evenly across layers.

        Flattens all anchor points, randomizes their order, and distributes them
        evenly across the specified number of layers using round-robin assignment.

        Args:
            anchor_points_by_segment: Dictionary mapping frame segment index to anchor points
            num_layers: Number of layers to distribute across

        Returns:
            Dictionary mapping layer number (1-indexed) to list of anchor points
        """
        # Flatten all anchor points
        all_anchors = [
            anchor for anchors in anchor_points_by_segment.values() for anchor in anchors
        ]

        # Randomize order
        random.shuffle(all_anchors)

        # Distribute to layers
        anchors_by_layer: dict[int, list[AnchorPoint]] = {
            layer: [] for layer in range(1, num_layers + 1)
        }

        for idx, anchor in enumerate(all_anchors):
            layer = (idx % num_layers) + 1
            anchor.layer = layer
            anchors_by_layer[layer].append(anchor)

        # Log distribution
        for layer, anchors in anchors_by_layer.items():
            logger.info(f"Layer {layer}: {len(anchors)} anchor points assigned")

        return anchors_by_layer

    def _calculate_layer_main_directions(
        self, num_layers: int, min_angle_deg: float, max_angle_deg: float
    ) -> dict[int, float]:
        """
        Calculate main direction for each layer.

        Distributes main directions evenly across the configured angle range.
        For a single layer, uses the midpoint. For multiple layers, uses linear
        interpolation to space directions evenly.

        Args:
            num_layers: Number of layers
            min_angle_deg: Minimum angle for main directions
            max_angle_deg: Maximum angle for main directions

        Returns:
            Dictionary mapping layer number (1-indexed) to main direction angle
        """
        layer_directions: dict[int, float] = {}

        if num_layers == 1:
            # Single layer: use midpoint
            layer_directions[1] = (min_angle_deg + max_angle_deg) / 2
        else:
            # Multiple layers: distribute evenly
            for layer_idx in range(num_layers):
                layer_num = layer_idx + 1
                # Linear interpolation across range
                t = layer_idx / (num_layers - 1)
                main_direction = min_angle_deg + t * (max_angle_deg - min_angle_deg)
                layer_directions[layer_num] = main_direction

        # Log directions
        for layer, direction in layer_directions.items():
            logger.info(f"Layer {layer} main direction: {direction:.1f}°")

        return layer_directions

    def _project_and_find_end_anchor(
        self,
        start_anchor: AnchorPoint,
        target_angle_deg: float,
        frame: RailingFrame,
        unused_anchors: list[AnchorPoint],
    ) -> AnchorPoint | None:
        """
        Project line from start anchor and find nearest unused anchor.

        Projects a line from the start anchor at the target angle in both directions
        to ensure intersection with the frame boundary. Then finds the nearest unused
        anchor to the intersection point on the opposite side.

        Args:
            start_anchor: The starting anchor point
            target_angle_deg: Target angle in degrees (0° = vertical, positive = clockwise)
            frame: The railing frame
            unused_anchors: List of unused anchor points

        Returns:
            End anchor if found, None otherwise
        """
        import math

        from shapely.geometry import LineString, Point

        # Convert angle to radians (0° = vertical, positive = clockwise)
        angle_rad = math.radians(target_angle_deg)

        # Project far enough to definitely cross frame
        projection_length = (
            max(
                frame.boundary.bounds[2] - frame.boundary.bounds[0],
                frame.boundary.bounds[3] - frame.boundary.bounds[1],
            )
            * 2
        )

        dx = projection_length * math.sin(angle_rad)
        dy = projection_length * math.cos(angle_rad)

        # Create line extending in both directions from start point
        projected_line = LineString(
            [
                (start_anchor.position[0] - dx, start_anchor.position[1] - dy),
                (start_anchor.position[0] + dx, start_anchor.position[1] + dy),
            ]
        )

        # Find intersection with frame boundary
        intersection = projected_line.intersection(frame.boundary.exterior)

        if intersection.is_empty:
            return None

        # Get intersection points (may be multipoint)
        if hasattr(intersection, "geoms"):
            intersection_points = list(intersection.geoms)
        else:
            intersection_points = [intersection]

        # Find the intersection point that is NOT near the start anchor (opposite side)
        start_point = Point(start_anchor.position)
        selected_intersection = None
        max_distance = 0.0

        for int_point in intersection_points:
            distance = start_point.distance(int_point)
            if distance > max_distance:
                max_distance = distance
                selected_intersection = int_point

        if selected_intersection is None:
            return None

        # Find nearest unused anchor to the selected intersection
        min_distance = float("inf")
        nearest_anchor = None

        for anchor in unused_anchors:
            if anchor is start_anchor:
                continue

            anchor_point = Point(anchor.position)
            distance = anchor_point.distance(selected_intersection)

            if distance < min_distance:
                min_distance = distance
                nearest_anchor = anchor

        return nearest_anchor

    def _validate_rod_constraints(
        self,
        rod_geometry: "LineString",
        layer_num: int,
        frame: RailingFrame,
        params: RandomGeneratorParametersV2,
        existing_layer_rods: list[Rod],
    ) -> bool:
        """
        Validate that rod meets all constraints.

        Checks length, boundary containment, angle deviation, and same-layer crossings.
        Updates statistics counters for each failed check.

        Args:
            rod_geometry: The rod geometry to validate
            layer_num: The layer number
            frame: The railing frame
            params: Generation parameters
            existing_layer_rods: Existing rods in the same layer

        Returns:
            True if valid, False otherwise
        """
        import math

        # Check length constraints
        rod_length = rod_geometry.length
        if rod_length < params.min_rod_length_cm:
            self.statistics.too_short += 1
            return False
        if rod_length > params.max_rod_length_cm:
            self.statistics.too_long += 1
            return False

        # Check boundary constraint
        if not rod_geometry.within(frame.boundary):
            self.statistics.outside_boundary += 1
            return False

        # Check angle deviation from vertical
        coords = list(rod_geometry.coords)
        dx = abs(coords[1][0] - coords[0][0])
        dy = abs(coords[1][1] - coords[0][1])
        if dy > 0:
            angle_rad = math.atan(dx / dy)
            angle_deg = math.degrees(angle_rad)
            if angle_deg > params.max_angle_deviation_deg:
                self.statistics.angle_too_large += 1
                return False

        # Check for crossings with same-layer rods
        for existing_rod in existing_layer_rods:
            if rod_geometry.crosses(existing_rod.geometry):
                self.statistics.crosses_same_layer += 1
                return False

        return True

    def _generate_layer_rods(
        self,
        layer_num: int,
        available_anchors: list[AnchorPoint],
        main_direction: float,
        frame: RailingFrame,
        params: RandomGeneratorParametersV2,
        existing_rods: list[Rod],
    ) -> tuple[list[Rod], int]:
        """
        Generate rods for a single layer.

        Uses the projection-and-search approach to create rods at angles close to
        the layer's main direction with random variation.

        Args:
            layer_num: Layer number (1-indexed)
            available_anchors: Available anchor points for this layer
            main_direction: Main direction angle for this layer
            frame: The railing frame
            params: Generation parameters
            existing_rods: Existing rods from all layers

        Returns:
            Tuple of (generated rods, iterations used)
        """
        from shapely.geometry import LineString

        logger.info(
            f"Starting generation for layer {layer_num} (main direction: {main_direction:.1f}°)"
        )

        # Calculate target rod count for this layer
        target_rods_for_layer = params.num_rods // params.num_layers
        if layer_num <= (params.num_rods % params.num_layers):
            target_rods_for_layer += 1

        layer_rods: list[Rod] = []
        unused_anchors = [a for a in available_anchors if not a.used]
        iterations = 0
        max_layer_iterations = params.max_iterations
        consecutive_failures = 0
        max_consecutive_failures = 100  # Stop if we fail 100 times in a row

        while len(layer_rods) < target_rods_for_layer and iterations < max_layer_iterations:
            iterations += 1

            # Check cancellation
            if self.is_cancelled():
                logger.info(f"Layer {layer_num} cancelled at iteration {iterations}")
                break

            # Progress logging every 1000 iterations
            if iterations % 1000 == 0:
                logger.info(
                    f"Layer {layer_num} progress: iteration {iterations}, "
                    f"{len(layer_rods)}/{target_rods_for_layer} rods, "
                    f"{len(unused_anchors)} unused anchors"
                )

            # Check if we have enough unused anchors
            if len(unused_anchors) < 2:
                logger.warning(
                    f"Layer {layer_num} stopped: only {len(unused_anchors)} unused anchors left"
                )
                break

            # Stop if too many consecutive failures (likely no valid rods possible)
            if consecutive_failures >= max_consecutive_failures:
                logger.warning(
                    f"Layer {layer_num} stopped: {consecutive_failures} consecutive failures, "
                    f"{len(unused_anchors)} unused anchors remaining"
                )
                break

            # Select random start anchor
            start_anchor = random.choice(unused_anchors)

            # Calculate target angle (main direction + random deviation)
            angle_offset = random.uniform(
                -params.random_angle_deviation_deg, params.random_angle_deviation_deg
            )
            target_angle = main_direction + angle_offset

            # Project and find end anchor
            end_anchor = self._project_and_find_end_anchor(
                start_anchor=start_anchor,
                target_angle_deg=target_angle,
                frame=frame,
                unused_anchors=unused_anchors,
            )

            if end_anchor is None:
                consecutive_failures += 1
                continue  # No suitable end anchor found

            # Create rod geometry
            rod_geometry = LineString([start_anchor.position, end_anchor.position])

            # Validate constraints
            if not self._validate_rod_constraints(
                rod_geometry=rod_geometry,
                layer_num=layer_num,
                frame=frame,
                params=params,
                existing_layer_rods=layer_rods,
            ):
                consecutive_failures += 1
                continue  # Constraints not met

            # Create rod
            rod = Rod(
                geometry=rod_geometry,
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=params.infill_weight_per_meter_kg_m,
                layer=layer_num,
            )

            # Mark anchors as used
            start_anchor.used = True
            end_anchor.used = True
            unused_anchors = [a for a in unused_anchors if not a.used]

            # Add to layer rods
            layer_rods.append(rod)

            # Reset consecutive failures counter on success
            consecutive_failures = 0

        if len(layer_rods) == target_rods_for_layer:
            logger.info(
                f"Layer {layer_num} complete: {len(layer_rods)} rods generated "
                f"in {iterations} iterations"
            )
        else:
            logger.warning(
                f"Layer {layer_num} incomplete: {len(layer_rods)}/{target_rods_for_layer} "
                f"rods generated in {iterations} iterations"
            )

        return layer_rods, iterations
