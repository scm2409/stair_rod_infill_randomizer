"""Evolutionary Infill Generator implementation.

A hybrid generator that combines uniform directional baseline generation
with iterative mutation and fitness-based selection for optimization.
"""

import logging
import time

from shapely.geometry import LineString, Point

from railing_generator.domain.anchor_point import AnchorPoint
from railing_generator.domain.evaluators.evaluator import Evaluator
from railing_generator.domain.evaluators.evaluator_factory import EvaluatorFactory
from railing_generator.domain.generation_progress import GenerationProgress
from railing_generator.domain.infill_generators.evolutionary_infill_generator_parameters import (
    EvolutionaryInfillGeneratorParameters,
)
from railing_generator.domain.infill_generators.generator import Generator
from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod

logger = logging.getLogger(__name__)


class EvolutionaryInfillGenerator(Generator):
    """
    Hybrid infill generator combining uniform baseline with evolutionary optimization.

    Key characteristics:
    - Structured Baseline: Uses uniform directional generation logic for initial arrangement
    - Iterative Optimization: Applies mutations and keeps improvements
    - Fitness-Driven: Uses the existing evaluator system for scoring
    - Monotonic Improvement: Solution quality never decreases
    - Early Termination: Stops on stagnation, max iterations, or max duration

    The generator starts with a deterministic uniform baseline, then iteratively
    applies random modifications to rod endpoints, keeping only changes that
    improve the fitness score.
    """

    # Define the parameter type for this generator
    PARAMETER_TYPE = EvolutionaryInfillGeneratorParameters

    def __init__(self) -> None:
        """Initialize the evolutionary infill generator."""
        super().__init__()

    def generate(self, frame: RailingFrame, params: InfillGeneratorParameters) -> RailingInfill:
        """
        Generate optimized infill arrangement using evolutionary approach.

        Algorithm:
        1. Validate parameter type
        2. Create evaluator from nested parameters
        3. Generate baseline using uniform directional logic
        4. Evaluate baseline fitness and emit best_result_updated signal
        5. Run evolutionary optimization loop (mutation + selection)
        6. Return best result found

        Args:
            frame: The railing frame defining the boundary
            params: EvolutionaryInfillGeneratorParameters for generation

        Returns:
            RailingInfill containing the optimized rods

        Raises:
            ValueError: If parameters are not EvolutionaryInfillGeneratorParameters
            RuntimeError: If generation fails (e.g., constraints cannot be satisfied)

        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 6.1-6.5
        """
        # Validate and narrow parameter type (runtime check for type safety)
        if not isinstance(params, EvolutionaryInfillGeneratorParameters):
            raise ValueError(
                f"EvolutionaryInfillGenerator requires EvolutionaryInfillGeneratorParameters, "
                f"got {type(params).__name__}"
            )

        # Reset cancellation flag
        self.reset_cancellation()

        # Create evaluator from nested parameters
        evaluator = EvaluatorFactory.create_evaluator(params.evaluator)

        start_time = time.time()

        logger.info(
            f"Starting evolutionary generation: "
            f"num_rods={params.num_rods}, num_layers={params.num_layers}, "
            f"direction_range=[{params.main_direction_range_min_deg}°, "
            f"{params.main_direction_range_max_deg}°], "
            f"max_iterations={params.max_iterations}, "
            f"max_duration_sec={params.max_duration_sec}, "
            f"improvement_threshold={params.improvement_threshold}, "
            f"stagnation_limit={params.stagnation_limit}"
        )

        # Emit initial progress
        progress = GenerationProgress(iteration=0, elapsed_sec=0.0)
        self.progress_updated.emit(progress)

        # Phase 1: Generate baseline using uniform directional logic
        baseline_infill, anchor_points, layer_directions = self._generate_baseline(
            frame, params, evaluator, start_time
        )

        # The baseline is our current best
        current_best = baseline_infill
        best_fitness = baseline_infill.fitness_score or 0.0
        current_anchor_points = anchor_points

        # Emit best_result_updated with baseline
        self.best_result_updated.emit(current_best)

        logger.info(f"Baseline created with fitness_score={best_fitness:.4f}")

        # Phase 2: Evolutionary optimization loop
        # Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
        stagnation_counter = 0
        iteration = 0
        improvements_found = 0

        while True:
            # Check termination conditions (Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6)
            elapsed = time.time() - start_time

            # Check max_iterations limit (Requirements: 5.1, 5.3)
            if iteration >= params.max_iterations:
                logger.info(f"Stopping: max_iterations ({params.max_iterations}) reached")
                break

            # Check max_duration_sec limit (Requirements: 5.2, 5.4)
            if elapsed > params.max_duration_sec:
                logger.info(
                    f"Stopping: max_duration_sec ({params.max_duration_sec}s) exceeded "
                    f"(elapsed: {elapsed:.2f}s)"
                )
                break

            # Check stagnation_limit (Requirements: 5.5, 5.6)
            if stagnation_counter >= params.stagnation_limit:
                logger.info(
                    f"Stopping: stagnation_limit ({params.stagnation_limit}) reached "
                    f"after {iteration - 1} iterations"
                )
                break

            # Check cancellation flag (Requirements: 6.5)
            if self.is_cancelled():
                logger.info("Generation cancelled by user")
                break

            # Mutate the current arrangement (Requirements: 3.1, 3.8)
            mutated_infill, mutated_anchors = self._mutate_arrangement(
                current_best, current_anchor_points, frame, params.num_layers
            )

            # Evaluate mutated arrangement (Requirements: 4.1)
            mutated_fitness = evaluator.evaluate(mutated_infill, frame)

            # Selection: keep if improved by at least improvement_threshold
            # (Requirements: 4.2, 4.3)
            if mutated_fitness > best_fitness + params.improvement_threshold:
                # Accept mutation as new baseline (Requirements: 4.2, 4.4, 4.5)
                current_best = RailingInfill(
                    rods=mutated_infill.rods,
                    fitness_score=mutated_fitness,
                    iteration_count=iteration,
                    duration_sec=elapsed,
                    anchor_points=mutated_anchors,
                    is_complete=True,
                )
                current_anchor_points = mutated_anchors
                old_fitness = best_fitness
                best_fitness = mutated_fitness
                stagnation_counter = 0  # Reset stagnation counter (Requirements: 4.5)
                improvements_found += 1

                # Emit best_result_updated signal (Requirements: 4.4, 6.2)
                self.best_result_updated.emit(current_best)

                logger.info(
                    f"Iteration {iteration}: Improvement found! "
                    f"fitness {old_fitness:.4f} -> {best_fitness:.4f} "
                    f"(+{best_fitness - old_fitness:.4f})"
                )
            else:
                # Discard mutation, keep current baseline (Requirements: 4.3)
                stagnation_counter += 1

            # Emit progress_updated signal each iteration (Requirements: 6.1)
            progress = GenerationProgress(iteration=iteration, elapsed_sec=elapsed)
            self.progress_updated.emit(progress)

            # Increment iteration counter at the end of the loop
            iteration += 1

            # Log progress every 100 iterations (Requirements: 11.4)
            if iteration % 100 == 0:
                logger.info(
                    f"Progress: iteration {iteration}/{params.max_iterations}, "
                    f"elapsed {elapsed:.2f}s, best_fitness={best_fitness:.4f}, "
                    f"stagnation={stagnation_counter}/{params.stagnation_limit}"
                )

        # Calculate final duration
        elapsed = time.time() - start_time

        # Create final result
        final_infill = RailingInfill(
            rods=current_best.rods,
            fitness_score=best_fitness,
            iteration_count=iteration,
            duration_sec=elapsed,
            anchor_points=current_anchor_points,
            is_complete=True,
        )

        # Log final statistics (Requirements: 11.5, 11.6)
        logger.info(
            f"Generation complete: {len(final_infill.rods)} rods generated in {elapsed:.3f}s, "
            f"iterations={iteration}, improvements={improvements_found}, "
            f"final_fitness={best_fitness:.4f}"
        )

        # Emit generation_completed signal (Requirements: 6.3)
        self.generation_completed.emit(final_infill)

        return final_infill

    def _generate_baseline(
        self,
        frame: RailingFrame,
        params: EvolutionaryInfillGeneratorParameters,
        evaluator: Evaluator,
        start_time: float,
    ) -> tuple[RailingInfill, list[AnchorPoint], dict[int, float]]:
        """
        Generate baseline infill using uniform directional generation logic.

        This method reuses the logic from UniformDirectionalGenerator to create
        a structured starting point for evolutionary optimization.

        Args:
            frame: The railing frame defining the boundary
            params: Generation parameters
            evaluator: Evaluator for fitness scoring
            start_time: Generation start time for duration tracking

        Returns:
            Tuple of (baseline_infill, anchor_points, layer_directions)

        Raises:
            RuntimeError: If baseline generation fails

        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1
        """
        # Phase 1: Generate anchor grid (Requirements 2.1)
        anchor_points = self._generate_anchor_grid(frame, params)

        # Check if we have enough anchors for the requested rods
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

        # Phase 2: Calculate layer directions (Requirements 1.3)
        layer_directions = self._calculate_layer_directions(params)

        # Calculate rods per layer (Requirements 1.2)
        base_rods_per_layer = params.num_rods // params.num_layers
        extra_rods = params.num_rods % params.num_layers

        # Phase 3: Generate rods for each layer
        all_rods: list[Rod] = []

        for layer_num in range(1, params.num_layers + 1):
            # Check cancellation
            if self.is_cancelled():
                error_msg = "Generation cancelled"
                self.generation_failed.emit(error_msg)
                raise RuntimeError(error_msg)

            # Calculate target rods for this layer
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

        # Verify rod count matches requested
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
            iteration_count=1,
            duration_sec=elapsed,
            anchor_points=anchor_points,
            is_complete=True,
        )

        # Run evaluator and set fitness score
        fitness_score = evaluator.evaluate(infill, frame)

        # Create final infill with fitness score
        baseline_infill = RailingInfill(
            rods=all_rods,
            fitness_score=fitness_score,
            iteration_count=1,
            duration_sec=elapsed,
            anchor_points=anchor_points,
            is_complete=True,
        )

        return baseline_infill, anchor_points, layer_directions

    def _generate_anchor_grid(
        self, frame: RailingFrame, params: EvolutionaryInfillGeneratorParameters
    ) -> list[AnchorPoint]:
        """
        Generate a grid of evenly spaced anchor points along the frame boundary.

        Creates as many anchor points as the minimum distance constraint allows
        along the entire frame boundary. All anchors start as "free" (not assigned
        to any rod).

        Algorithm:
        1. Calculate total frame perimeter
        2. Calculate spacing based on min_anchor_distance_cm
        3. Place anchors at regular intervals along frame boundary
        4. Check and remove anchors that are too close at corners (Euclidean distance)
        5. All anchors start as "free" (not assigned to any rod)

        Args:
            frame: The railing frame defining the boundary
            params: Generation parameters containing min_anchor_distance_cm

        Returns:
            List of AnchorPoint objects, all marked as free (used=False)

        Requirements: 2.1
        """
        boundary = frame.boundary
        perimeter = boundary.exterior.length
        min_distance = params.min_anchor_distance_cm

        # Calculate number of anchors based on minimum distance constraint
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
        selected_points: list[Point] = []

        for i, point in enumerate(candidate_points):
            if selected_points:
                prev_point = selected_points[-1]
                if point.distance(prev_point) < min_distance:
                    continue

            selected_points.append(point)

        # Check if last point is too close to first (closed boundary)
        if len(selected_points) >= 2:
            first_point = selected_points[0]
            last_point = selected_points[-1]
            if first_point.distance(last_point) < min_distance:
                selected_points.pop()

        # Create AnchorPoint objects from selected points
        anchor_points: list[AnchorPoint] = []

        for point in selected_points:
            frame_segment_index, is_vertical, frame_segment_angle_deg = (
                self._find_frame_segment_for_point(frame, point)
            )

            anchor = AnchorPoint(
                position=point,
                frame_segment_index=frame_segment_index,
                is_vertical_segment=is_vertical,
                frame_segment_angle_deg=frame_segment_angle_deg,
                layer=None,
                used=False,
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

        Args:
            rod: The rod to classify

        Returns:
            True if vertical, False otherwise
        """
        coords = list(rod.geometry.coords)
        dx = abs(coords[1][0] - coords[0][0])
        dy = abs(coords[1][1] - coords[0][1])

        if dy > 0 and dx / dy < 0.1:
            return True
        return False

    def _calculate_layer_directions(
        self, params: EvolutionaryInfillGeneratorParameters
    ) -> dict[int, float]:
        """
        Calculate the main direction angle for each layer.

        For a single layer, uses the midpoint of the direction range.
        For multiple layers, distributes directions evenly across the range
        using linear interpolation.

        Args:
            params: Generation parameters containing direction range and num_layers

        Returns:
            Dictionary mapping layer number (1-based) to direction angle in degrees

        Requirements: 1.3
        """
        num_layers = params.num_layers
        min_deg = params.main_direction_range_min_deg
        max_deg = params.main_direction_range_max_deg

        layer_directions: dict[int, float] = {}

        if num_layers == 1:
            midpoint = (min_deg + max_deg) / 2.0
            layer_directions[1] = midpoint
            logger.debug(f"Single layer direction: {midpoint:.2f}°")
        else:
            for i in range(num_layers):
                t = i / (num_layers - 1)
                direction = min_deg + t * (max_deg - min_deg)
                layer_directions[i + 1] = direction
                logger.debug(f"Layer {i + 1} direction: {direction:.2f}° (t={t:.3f})")

        return layer_directions

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

        dx = x - cx
        dy = y - cy

        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a

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

        Requirements: 1.2, 1.4
        """
        import math

        logger.info(
            f"Generating layer {layer_num}: target={target_rods} rods, "
            f"direction={direction_deg:.1f}°"
        )

        if target_rods <= 0:
            return []

        centroid = frame.boundary.centroid
        cx, cy = centroid.x, centroid.y

        rotation_angle_rad = math.radians(-direction_deg)

        rotated_anchors: list[tuple[float, float, int, AnchorPoint]] = []
        for idx, anchor in enumerate(anchor_points):
            rx, ry = self._rotate_point(
                anchor.position.x, anchor.position.y, rotation_angle_rad, cx, cy
            )
            rotated_anchors.append((rx, ry, idx, anchor))

        rotated_coords = [
            self._rotate_point(x, y, rotation_angle_rad, cx, cy)
            for x, y in frame.boundary.exterior.coords
        ]
        rotated_xs = [x for x, y in rotated_coords]
        min_x_rotated = min(rotated_xs)
        max_x_rotated = max(rotated_xs)

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

        free_rotated_anchors = [
            (rx, ry, idx, anchor) for rx, ry, idx, anchor in rotated_anchors if not anchor.used
        ]

        if len(free_rotated_anchors) < 2:
            logger.warning(f"Layer {layer_num}: Not enough free anchors")
            return []

        rod_x_positions: list[float] = []

        if target_rods == 1:
            rod_x_positions = [(valid_x_min + valid_x_max) / 2.0]
        else:
            spacing = valid_extent / (target_rods - 1)
            for i in range(target_rods):
                x_pos = valid_x_min + i * spacing
                rod_x_positions.append(x_pos)

        logger.debug(
            f"Layer {layer_num}: Rod x-positions (rotated space): "
            f"{[f'{x:.2f}' for x in rod_x_positions]}"
        )

        layer_rods: list[Rod] = []

        for rod_x in rod_x_positions:
            anchor_pair = self._find_opposite_anchors_at_x(
                rod_x, free_rotated_anchors, rotated_anchors
            )
            if anchor_pair is None:
                logger.debug(f"Layer {layer_num}: No anchor pair found for x={rod_x:.2f}")
                continue

            high_anchor, low_anchor = anchor_pair

            high_anchor.used = True
            low_anchor.used = True

            free_rotated_anchors = [
                (rx, ry, idx, a) for rx, ry, idx, a in free_rotated_anchors if not a.used
            ]

            rod_geometry = LineString(
                [high_anchor.position.coords[0], low_anchor.position.coords[0]]
            )

            temp_rod = Rod(
                geometry=rod_geometry,
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=weight_kg_m,
                layer=layer_num,
            )

            start_cut_angle, end_cut_angle = self._calculate_cut_angles(
                rod_angle_deg=temp_rod.angle_from_vertical_deg,
                start_anchor=high_anchor,
                end_anchor=low_anchor,
            )

            rod = Rod(
                geometry=rod_geometry,
                start_cut_angle_deg=start_cut_angle,
                end_cut_angle_deg=end_cut_angle,
                weight_kg_m=weight_kg_m,
                layer=layer_num,
            )

            if self._rod_crosses_existing_rods(rod, layer_rods):
                high_anchor.used = False
                low_anchor.used = False
                free_rotated_anchors = [
                    (rx, ry, idx, a) for rx, ry, idx, a in rotated_anchors if not a.used
                ]
                logger.debug(f"Layer {layer_num}: Rod would cross existing rods")
                continue

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

        Args:
            target_x: Target x-coordinate in rotated space
            free_rotated_anchors: List of unused (rotated_x, rotated_y, idx, anchor) tuples
            all_rotated_anchors: All anchors for reference

        Returns:
            Tuple of (high_y_anchor, low_y_anchor) or None if not found
        """
        if len(free_rotated_anchors) < 2:
            return None

        x_coords = [rx for rx, ry, idx, a in free_rotated_anchors]
        if not x_coords:
            return None

        x_coords_sorted = sorted(x_coords)
        if len(x_coords_sorted) > 1:
            avg_spacing = (x_coords_sorted[-1] - x_coords_sorted[0]) / (len(x_coords_sorted) - 1)
            x_tolerance = max(avg_spacing * 1.5, 10.0)
        else:
            x_tolerance = 50.0

        nearby_anchors = [
            (rx, ry, idx, anchor)
            for rx, ry, idx, anchor in free_rotated_anchors
            if abs(rx - target_x) <= x_tolerance
        ]

        if len(nearby_anchors) < 2:
            sorted_by_x_dist = sorted(free_rotated_anchors, key=lambda a: abs(a[0] - target_x))
            nearby_anchors = sorted_by_x_dist[: min(10, len(sorted_by_x_dist))]

        if len(nearby_anchors) < 2:
            return None

        high_y_data = max(nearby_anchors, key=lambda a: a[1])
        low_y_data = min(nearby_anchors, key=lambda a: a[1])

        if high_y_data[3] is low_y_data[3]:
            return None

        return (high_y_data[3], low_y_data[3])

    def _calculate_cut_angles(
        self,
        rod_angle_deg: float,
        start_anchor: AnchorPoint,
        end_anchor: AnchorPoint,
    ) -> tuple[float, float]:
        """
        Calculate start and end cut angles for a rod based on frame segment angles.

        Args:
            rod_angle_deg: Angle of the rod from vertical in degrees
            start_anchor: Starting anchor point with frame segment angle
            end_anchor: Ending anchor point with frame segment angle

        Returns:
            Tuple of (start_cut_angle_deg, end_cut_angle_deg)
        """
        start_cut_angle = rod_angle_deg - start_anchor.frame_segment_angle_deg
        end_cut_angle = rod_angle_deg - end_anchor.frame_segment_angle_deg

        def normalize_cut_angle(angle: float) -> float:
            while angle > 180:
                angle -= 360
            while angle < -180:
                angle += 360

            if angle > 90:
                angle = 180 - angle
            elif angle < -90:
                angle = -180 - angle

            return angle

        start_cut_angle = normalize_cut_angle(start_cut_angle)
        end_cut_angle = normalize_cut_angle(end_cut_angle)

        return start_cut_angle, end_cut_angle

    def _rod_crosses_existing_rods(self, new_rod: Rod, existing_rods: list[Rod]) -> bool:
        """
        Check if a new rod crosses any existing rods.

        Args:
            new_rod: The rod to check
            existing_rods: List of existing rods to check against

        Returns:
            True if the new rod crosses any existing rod, False otherwise

        Requirements: 7.3
        """
        for existing_rod in existing_rods:
            intersection = new_rod.geometry.intersection(existing_rod.geometry)

            if intersection.is_empty:
                continue

            if intersection.geom_type == "Point":
                is_at_endpoint = (
                    intersection.equals(new_rod.start_point)
                    or intersection.equals(new_rod.end_point)
                    or intersection.equals(existing_rod.start_point)
                    or intersection.equals(existing_rod.end_point)
                )

                if not is_at_endpoint:
                    logger.debug(
                        f"Rod crossing detected at {intersection}: "
                        f"new rod from {new_rod.start_point} to {new_rod.end_point}, "
                        f"existing rod from {existing_rod.start_point} to {existing_rod.end_point}"
                    )
                    return True

            elif intersection.geom_type == "LineString":
                logger.debug(
                    f"Rod overlap detected: "
                    f"new rod from {new_rod.start_point} to {new_rod.end_point}, "
                    f"existing rod from {existing_rod.start_point} to {existing_rod.end_point}"
                )
                return True

        return False

    def verify_rod_endpoints_on_boundary(
        self, rod: Rod, frame: RailingFrame, tolerance: float = 0.1
    ) -> bool:
        """
        Verify that both endpoints of a rod lie on the frame boundary.

        Args:
            rod: The rod to verify
            frame: The railing frame defining the boundary
            tolerance: Maximum distance from boundary to consider "on boundary" (in cm)

        Returns:
            True if both endpoints are on the boundary, False otherwise

        Requirements: 7.1
        """
        boundary = frame.boundary.exterior

        # Check start point
        start_distance = boundary.distance(rod.start_point)
        if start_distance > tolerance:
            logger.debug(
                f"Rod start point {rod.start_point} is {start_distance:.4f}cm "
                f"from boundary (tolerance: {tolerance}cm)"
            )
            return False

        # Check end point
        end_distance = boundary.distance(rod.end_point)
        if end_distance > tolerance:
            logger.debug(
                f"Rod end point {rod.end_point} is {end_distance:.4f}cm "
                f"from boundary (tolerance: {tolerance}cm)"
            )
            return False

        return True

    def verify_rod_within_boundary(
        self, rod: Rod, frame: RailingFrame, tolerance: float = 0.1
    ) -> bool:
        """
        Verify that the entire rod geometry is within the frame boundary.

        Args:
            rod: The rod to verify
            frame: The railing frame defining the boundary
            tolerance: Maximum distance outside boundary to consider "within" (in cm)

        Returns:
            True if the rod is within the boundary, False otherwise

        Requirements: 7.2
        """
        boundary = frame.boundary

        # Check if the rod geometry is within the boundary polygon
        # Using buffer with tolerance to handle floating point precision
        buffered_boundary = boundary.buffer(tolerance)

        if not buffered_boundary.contains(rod.geometry):
            # Check if it's just slightly outside due to floating point
            if rod.geometry.within(buffered_boundary):
                return True

            logger.debug(
                f"Rod from {rod.start_point} to {rod.end_point} is not within frame boundary"
            )
            return False

        return True

    def verify_rod_constraints(self, rod: Rod, frame: RailingFrame, tolerance: float = 0.1) -> bool:
        """
        Verify that a rod satisfies all boundary constraints.

        This method combines endpoint and geometry checks:
        1. Both endpoints must be on the frame boundary
        2. The entire rod geometry must be within the frame boundary

        Args:
            rod: The rod to verify
            frame: The railing frame defining the boundary
            tolerance: Maximum distance tolerance for boundary checks (in cm)

        Returns:
            True if all constraints are satisfied, False otherwise

        Requirements: 7.1, 7.2
        """
        # Check endpoints on boundary
        if not self.verify_rod_endpoints_on_boundary(rod, frame, tolerance):
            return False

        # Check rod within boundary
        if not self.verify_rod_within_boundary(rod, frame, tolerance):
            return False

        return True

    def _sort_anchors_by_boundary_position(
        self, anchor_points: list[AnchorPoint], frame: RailingFrame
    ) -> list[tuple[float, AnchorPoint]]:
        """
        Sort anchor points by their position along the frame boundary.

        Args:
            anchor_points: List of anchor points to sort
            frame: The railing frame defining the boundary

        Returns:
            List of (distance_along_boundary, anchor) tuples sorted by distance
        """
        boundary = frame.boundary.exterior
        anchors_with_distance: list[tuple[float, AnchorPoint]] = []

        for anchor in anchor_points:
            # Project the anchor position onto the boundary to get distance along boundary
            distance = boundary.project(anchor.position)
            anchors_with_distance.append((distance, anchor))

        # Sort by distance along boundary
        anchors_with_distance.sort(key=lambda x: x[0])

        return anchors_with_distance

    def _find_next_free_anchor(
        self,
        current_anchor: AnchorPoint,
        direction: str,
        anchor_points: list[AnchorPoint],
        frame: RailingFrame,
    ) -> AnchorPoint | None:
        """
        Find the nearest free anchor point along the frame boundary in a given direction.

        Searches along the frame boundary in the specified direction (clockwise or
        counterclockwise) to find the next anchor point that is not currently used.
        Handles wrap-around at boundary ends.

        Args:
            current_anchor: The anchor point to start searching from
            direction: Search direction - "cw" for clockwise, "ccw" for counterclockwise
            anchor_points: List of all anchor points
            frame: The railing frame defining the boundary

        Returns:
            The next free AnchorPoint in the specified direction, or None if no free
            anchor is found.

        Requirements: 3.2, 3.3
        """
        # Sort anchors by position along boundary
        sorted_anchors = self._sort_anchors_by_boundary_position(anchor_points, frame)

        # Find the index of the current anchor in the sorted list
        current_index = -1
        for i, (_, anchor) in enumerate(sorted_anchors):
            if anchor is current_anchor:
                current_index = i
                break

        if current_index == -1:
            # Current anchor not found in list - shouldn't happen
            logger.warning("Current anchor not found in anchor list")
            return None

        num_anchors = len(sorted_anchors)

        if direction == "cw":
            # Search forward (clockwise), wrapping around
            for offset in range(1, num_anchors):
                idx = (current_index + offset) % num_anchors
                _, candidate_anchor = sorted_anchors[idx]
                if not candidate_anchor.used:
                    return candidate_anchor
        else:  # ccw
            # Search backward (counterclockwise), wrapping around
            for offset in range(1, num_anchors):
                idx = (current_index - offset) % num_anchors
                _, candidate_anchor = sorted_anchors[idx]
                if not candidate_anchor.used:
                    return candidate_anchor

        # No free anchor found
        return None

    def _find_anchor_at_position(
        self, position: Point, anchor_points: list[AnchorPoint], tolerance: float = 0.1
    ) -> AnchorPoint | None:
        """
        Find the anchor point at a given position.

        Args:
            position: The position to search for
            anchor_points: List of anchor points to search
            tolerance: Maximum distance to consider a match (in cm)

        Returns:
            The AnchorPoint at the position, or None if not found
        """
        for anchor in anchor_points:
            if anchor.position.distance(position) < tolerance:
                return anchor
        return None

    def _mutate_rod(
        self,
        rod: Rod,
        anchor_points: list[AnchorPoint],
        same_layer_rods: list[Rod],
        frame: RailingFrame,
    ) -> bool:
        """
        Mutate a single rod by moving its endpoints to neighboring free anchor points.

        This method attempts to move both endpoints of a rod to the next free anchor
        points along the frame boundary. If the mutation would cause a same-layer
        crossing, the mutation is undone and the rod remains unchanged.

        Algorithm:
        1. Find the anchor points at the rod's current endpoints
        2. Choose a random direction (clockwise or counterclockwise)
        3. Find next free anchors for both endpoints
        4. If no free anchors found, return without mutation
        5. If new anchors are the same point, return without mutation
        6. Release original anchor points (mark free, clear layer)
        7. Create mutated rod geometry
        8. Check for same-layer crossings
        9. If crossing detected: restore original anchors and return False
        10. If valid: claim new anchors and update rod geometry, return True

        Args:
            rod: The rod to mutate (will be modified in place if mutation succeeds)
            anchor_points: List of all anchor points (will be modified)
            same_layer_rods: List of other rods in the same layer (for crossing check)
            frame: The railing frame defining the boundary

        Returns:
            True if mutation was applied, False if mutation was rejected or not possible

        Requirements: 2.3, 2.4, 2.5, 3.2, 3.4, 3.5, 3.6, 3.7
        """
        import random

        # Find anchor points at rod endpoints
        start_anchor = self._find_anchor_at_position(rod.start_point, anchor_points)
        end_anchor = self._find_anchor_at_position(rod.end_point, anchor_points)

        if start_anchor is None or end_anchor is None:
            logger.debug("Could not find anchor points for rod endpoints")
            return False

        # Choose random direction (clockwise or counterclockwise)
        direction = random.choice(["cw", "ccw"])

        # Find next free anchors for both endpoints
        # First, temporarily release the current anchors so they can be found as "free"
        # if the search wraps around
        original_start_used = start_anchor.used
        original_start_layer = start_anchor.layer
        original_end_used = end_anchor.used
        original_end_layer = end_anchor.layer

        # Release original anchors temporarily
        start_anchor.used = False
        start_anchor.layer = None
        end_anchor.used = False
        end_anchor.layer = None

        # Find next free anchors
        new_start_anchor = self._find_next_free_anchor(
            start_anchor, direction, anchor_points, frame
        )
        new_end_anchor = self._find_next_free_anchor(end_anchor, direction, anchor_points, frame)

        # If no free anchors found, restore original state and return
        if new_start_anchor is None or new_end_anchor is None:
            start_anchor.used = original_start_used
            start_anchor.layer = original_start_layer
            end_anchor.used = original_end_used
            end_anchor.layer = original_end_layer
            return False

        # If new anchors are the same point, would create zero-length rod
        if new_start_anchor is new_end_anchor:
            start_anchor.used = original_start_used
            start_anchor.layer = original_start_layer
            end_anchor.used = original_end_used
            end_anchor.layer = original_end_layer
            return False

        # Create mutated rod geometry
        mutated_geometry = LineString(
            [new_start_anchor.position.coords[0], new_end_anchor.position.coords[0]]
        )

        # Create temporary rod for crossing check
        temp_rod = Rod(
            geometry=mutated_geometry,
            start_cut_angle_deg=rod.start_cut_angle_deg,
            end_cut_angle_deg=rod.end_cut_angle_deg,
            weight_kg_m=rod.weight_kg_m,
            layer=rod.layer,
        )

        # Check for same-layer crossings (exclude the current rod from the check)
        other_rods = [r for r in same_layer_rods if r is not rod]
        if self._rod_crosses_existing_rods(temp_rod, other_rods):
            # Crossing detected - restore original anchors and reject mutation
            start_anchor.used = original_start_used
            start_anchor.layer = original_start_layer
            end_anchor.used = original_end_used
            end_anchor.layer = original_end_layer
            logger.debug("Mutation rejected: would cause same-layer crossing")
            return False

        # Mutation is valid - claim new anchors
        new_start_anchor.used = True
        new_start_anchor.layer = rod.layer
        new_end_anchor.used = True
        new_end_anchor.layer = rod.layer

        # Calculate new cut angles
        start_cut_angle, end_cut_angle = self._calculate_cut_angles(
            rod_angle_deg=temp_rod.angle_from_vertical_deg,
            start_anchor=new_start_anchor,
            end_anchor=new_end_anchor,
        )

        # Update rod geometry in place
        # Note: Rod is a Pydantic model, so we need to use model_copy or create new
        # Since we're modifying in place, we'll update the geometry attribute directly
        # This requires the model to not be frozen
        object.__setattr__(rod, "geometry", mutated_geometry)
        object.__setattr__(rod, "start_cut_angle_deg", start_cut_angle)
        object.__setattr__(rod, "end_cut_angle_deg", end_cut_angle)

        logger.debug(
            f"Mutation applied: rod moved from "
            f"({start_anchor.position.x:.1f}, {start_anchor.position.y:.1f})-"
            f"({end_anchor.position.x:.1f}, {end_anchor.position.y:.1f}) to "
            f"({new_start_anchor.position.x:.1f}, {new_start_anchor.position.y:.1f})-"
            f"({new_end_anchor.position.x:.1f}, {new_end_anchor.position.y:.1f})"
        )

        return True

    def _deep_copy_anchor_points(self, anchor_points: list[AnchorPoint]) -> list[AnchorPoint]:
        """
        Create a deep copy of anchor points list.

        Args:
            anchor_points: List of anchor points to copy

        Returns:
            New list with copied AnchorPoint objects
        """
        copied_anchors: list[AnchorPoint] = []
        for anchor in anchor_points:
            copied_anchor = AnchorPoint(
                position=Point(anchor.position.x, anchor.position.y),
                frame_segment_index=anchor.frame_segment_index,
                is_vertical_segment=anchor.is_vertical_segment,
                frame_segment_angle_deg=anchor.frame_segment_angle_deg,
                layer=anchor.layer,
                used=anchor.used,
            )
            copied_anchors.append(copied_anchor)
        return copied_anchors

    def _deep_copy_rods(self, rods: list[Rod]) -> list[Rod]:
        """
        Create a deep copy of rods list.

        Args:
            rods: List of rods to copy

        Returns:
            New list with copied Rod objects
        """
        copied_rods: list[Rod] = []
        for rod in rods:
            copied_rod = Rod(
                geometry=LineString(list(rod.geometry.coords)),
                start_cut_angle_deg=rod.start_cut_angle_deg,
                end_cut_angle_deg=rod.end_cut_angle_deg,
                weight_kg_m=rod.weight_kg_m,
                layer=rod.layer,
            )
            copied_rods.append(copied_rod)
        return copied_rods

    def _mutate_arrangement(
        self,
        infill: RailingInfill,
        anchor_points: list[AnchorPoint],
        frame: RailingFrame,
        num_layers: int,
    ) -> tuple[RailingInfill, list[AnchorPoint]]:
        """
        Mutate the entire infill arrangement by processing each layer sequentially.

        Creates deep copies of the current arrangement and anchor state, then
        processes each layer sequentially, attempting to mutate each rod.

        Algorithm:
        1. Deep copy current arrangement (rods) and anchor state
        2. For each layer (1 to num_layers):
           a. Get all rods in this layer
           b. For each rod in layer: call _mutate_rod()
        3. Return mutated arrangement and anchor state

        Args:
            infill: The current infill arrangement
            anchor_points: The current anchor point state
            frame: The railing frame defining the boundary
            num_layers: Number of layers in the arrangement

        Returns:
            Tuple of (mutated_infill, mutated_anchor_points)

        Requirements: 3.1, 3.8
        """
        # Deep copy current arrangement and anchor state
        mutated_anchors = self._deep_copy_anchor_points(anchor_points)
        mutated_rods = self._deep_copy_rods(infill.rods)

        # Process each layer sequentially
        for layer_num in range(1, num_layers + 1):
            # Get all rods in this layer
            layer_rods = [rod for rod in mutated_rods if rod.layer == layer_num]

            # For each rod in layer: attempt mutation
            for rod in layer_rods:
                self._mutate_rod(rod, mutated_anchors, layer_rods, frame)

        # Create mutated infill
        mutated_infill = RailingInfill(
            rods=mutated_rods,
            fitness_score=None,  # Will be evaluated later
            iteration_count=infill.iteration_count,
            duration_sec=infill.duration_sec,
            anchor_points=mutated_anchors,
            is_complete=infill.is_complete,
        )

        return mutated_infill, mutated_anchors
