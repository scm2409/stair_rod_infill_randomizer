"""Random infill generator implementation."""

import logging
import random
import time

from shapely.geometry import LineString

from railing_generator.domain.infill_generators.generation_statistics import (
    GenerationStatistics,
)
from railing_generator.domain.infill_generators.generator import Generator
from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorParameters,
)
from railing_generator.domain.infill_generators.random_generator_parameters import (
    RandomGeneratorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod

logger = logging.getLogger(__name__)


class RandomGenerator(Generator):
    """
    Random infill generator with simple random placement.

    This is a simplified version without quality evaluation.
    It generates random rod arrangements that respect basic constraints:
    - Rods within same layer do not cross
    - Rods remain within frame boundary
    - Rods are anchored to the frame
    """

    # Define the parameter type for this generator
    PARAMETER_TYPE = RandomGeneratorParameters

    def __init__(self) -> None:
        """Initialize the random generator."""
        super().__init__()
        self.statistics = GenerationStatistics()

    def get_statistics(self) -> GenerationStatistics:
        """
        Get the statistics from the last generation run.

        Returns:
            GenerationStatistics object with metrics from last generation
        """
        return self.statistics

    def generate(self, frame: RailingFrame, params: InfillGeneratorParameters) -> RailingInfill:
        """
        Generate random infill arrangement within the frame.

        Args:
            frame: The railing frame defining the boundary
            params: RandomGeneratorParameters for generation

        Returns:
            RailingInfill containing the generated rods

        Raises:
            ValueError: If parameters are not RandomGeneratorParameters
            RuntimeError: If generation fails
        """
        # Validate and narrow parameter type (runtime check for type safety)
        if not isinstance(params, RandomGeneratorParameters):
            raise ValueError(
                f"RandomGenerator requires RandomGeneratorParameters, got {type(params).__name__}"
            )
        # After isinstance check, mypy knows params is RandomGeneratorParameters
        # No explicit cast needed - type narrowing handles it

        # Reset cancellation flag
        self.reset_cancellation()

        # Initialize statistics for this generation run
        self.statistics = GenerationStatistics(rods_requested=params.num_rods)

        # Start generation
        start_time = time.time()
        best_infill: RailingInfill | None = None
        iteration = 0

        try:
            # Simple generation loop (no quality evaluation yet)
            while iteration < params.max_iterations:
                # Check cancellation
                if self.is_cancelled():
                    if best_infill is not None:
                        return best_infill
                    raise RuntimeError("Generation cancelled before any valid result")

                # Check duration limit
                elapsed = time.time() - start_time
                if elapsed > params.max_duration_sec:
                    if best_infill is not None:
                        return best_infill
                    raise RuntimeError("Generation timeout before any valid result")

                iteration += 1

                # Generate a random arrangement
                try:
                    rods = self._generate_random_arrangement(frame, params)

                    # Create infill result
                    infill = RailingInfill(
                        rods=rods,
                        fitness_score=None,  # No quality evaluation yet
                        iteration_count=iteration,
                        duration_sec=elapsed,
                    )

                    # Update best result
                    best_infill = infill

                    # Emit progress
                    self.progress_updated.emit(
                        {
                            "iteration": iteration,
                            "best_fitness": None,
                            "elapsed_sec": elapsed,
                        }
                    )

                    # Emit best result update
                    self.best_result_updated.emit(infill)

                    # Update statistics
                    self.statistics.iterations_used = iteration
                    self.statistics.duration_sec = elapsed

                    # Log statistics
                    logger.info(f"Generation successful:\n{self.statistics}")

                    # For now, accept the first valid arrangement
                    # (quality evaluation will be added in Task 6)
                    self.generation_completed.emit(infill)
                    return infill

                except ValueError:
                    # Failed to generate valid arrangement, try again
                    continue

            # Max iterations reached without valid result
            if best_infill is not None:
                self.statistics.iterations_used = iteration
                self.statistics.duration_sec = time.time() - start_time
                logger.info(f"Generation completed (max iterations):\n{self.statistics}")
                self.generation_completed.emit(best_infill)
                return best_infill

            # Update statistics for failure case
            self.statistics.iterations_used = iteration
            self.statistics.duration_sec = time.time() - start_time
            logger.info(f"Generation failed:\n{self.statistics}")

            raise RuntimeError(
                f"Failed to generate valid arrangement after {params.max_iterations} iterations"
            )

        except Exception as e:
            error_msg = f"Generation failed: {str(e)}"
            self.generation_failed.emit(error_msg)
            raise RuntimeError(error_msg) from e

    def _generate_random_arrangement(
        self, frame: RailingFrame, params: RandomGeneratorParameters
    ) -> list[Rod]:
        """
        Generate a random rod arrangement.

        Args:
            frame: The railing frame
            params: Generation parameters

        Returns:
            List of Rod objects

        Raises:
            ValueError: If unable to generate valid arrangement
        """
        import math

        from shapely.geometry import Point

        # Get frame boundary as LineString for anchor point selection
        frame_boundary = LineString(frame.boundary.exterior.coords)
        frame_length = frame_boundary.length

        # Generate MORE anchor points than strictly needed (5x multiplier for better success rate)
        # This gives us a larger pool to find valid rod pairs from
        num_anchor_points = max(params.num_rods * 5, 20)
        anchor_points = self._generate_anchor_points(
            frame_boundary, frame_length, num_anchor_points, params.min_anchor_distance_cm
        )

        if len(anchor_points) < params.num_rods * 2:
            raise ValueError(
                f"Could not generate enough anchor points: {len(anchor_points)} < {params.num_rods * 2}"
            )

        # Organize rods by layer
        rods_by_layer: dict[int, list[Rod]] = {
            layer: [] for layer in range(1, params.num_layers + 1)
        }

        # Calculate target rods per layer for even distribution
        target_rods_per_layer = params.num_rods // params.num_layers
        remaining_rods = params.num_rods % params.num_layers

        # Create a list of target counts per layer
        layer_targets = [target_rods_per_layer] * params.num_layers
        for i in range(remaining_rods):
            layer_targets[i] += 1

        # Shuffle anchor points for randomness
        random.shuffle(anchor_points)

        # Track which anchors have been used
        used_anchors: set[int] = set()

        # Generate rods by pairing anchor points
        rods: list[Rod] = []

        # Track consecutive failures to detect when we should give up early
        consecutive_failures = 0
        max_consecutive_failures = 50

        for rod_attempt in range(params.num_rods):
            # Select layer with fewest rods to maintain even distribution
            layer = self._select_layer_for_even_distribution(rods_by_layer, layer_targets)

            # Get list of available anchors once per rod attempt (more efficient)
            available_anchors = [i for i in range(len(anchor_points)) if i not in used_anchors]

            if len(available_anchors) < 2:
                self.statistics.no_anchors_left += 1
                break

            # Try to create a valid rod using available anchor points
            max_attempts = min(100, len(available_anchors) * (len(available_anchors) - 1) // 2)
            rod_created = False

            for attempt in range(max_attempts):
                # Early exit if we've had too many consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    break

                # Randomly select two different anchor points
                # Use random.sample for efficiency (no need to remove and re-add)
                anchor1_idx, anchor2_idx = random.sample(available_anchors, 2)

                # Get the anchor points
                anchor1 = Point(anchor_points[anchor1_idx])
                anchor2 = Point(anchor_points[anchor2_idx])

                # Create rod geometry
                rod_geometry = LineString([anchor1.coords[0], anchor2.coords[0]])

                # Check length constraints
                rod_length = rod_geometry.length
                if rod_length < params.min_rod_length_cm:
                    self.statistics.too_short += 1
                    consecutive_failures += 1
                    continue
                if rod_length > params.max_rod_length_cm:
                    self.statistics.too_long += 1
                    consecutive_failures += 1
                    continue

                # Check if rod is within boundary
                if not rod_geometry.within(frame.boundary):
                    self.statistics.outside_boundary += 1
                    consecutive_failures += 1
                    continue

                # Check angle deviation from vertical
                dx = anchor2.x - anchor1.x
                dy = anchor2.y - anchor1.y
                if dx == 0:
                    angle_deg = 0.0
                else:
                    angle_rad = math.atan(abs(dx) / abs(dy)) if dy != 0 else math.pi / 2
                    angle_deg = math.degrees(angle_rad)

                if angle_deg > params.max_angle_deviation_deg:
                    self.statistics.angle_too_large += 1
                    consecutive_failures += 1
                    continue

                # Check for crossings with same-layer rods
                crosses_same_layer = False
                for existing_rod in rods_by_layer[layer]:
                    if rod_geometry.crosses(existing_rod.geometry):
                        crosses_same_layer = True
                        break

                if crosses_same_layer:
                    self.statistics.crosses_same_layer += 1
                    consecutive_failures += 1
                    continue

                # Create rod
                rod = Rod(
                    geometry=rod_geometry,
                    start_cut_angle_deg=0.0,
                    end_cut_angle_deg=0.0,
                    weight_kg_m=params.infill_weight_per_meter_kg_m,
                    layer=layer,
                )

                # Add to layer and overall list
                rods_by_layer[layer].append(rod)
                rods.append(rod)

                # Mark these anchors as used
                used_anchors.add(anchor1_idx)
                used_anchors.add(anchor2_idx)

                # Reset consecutive failures on success
                consecutive_failures = 0
                rod_created = True
                break

            # If we failed to create a rod after all attempts, give up
            if not rod_created:
                break

        # Update statistics with final rod count
        self.statistics.rods_created = len(rods)

        # Check if we generated ALL requested rods
        if len(rods) < params.num_rods:
            raise ValueError(
                f"Only generated {len(rods)} rods out of {params.num_rods} requested. "
                f"Generation incomplete."
            )

        return rods

    def _generate_anchor_points(
        self, frame_boundary: LineString, frame_length: float, num_points: int, min_distance: float
    ) -> list[tuple[float, float]]:
        """
        Pre-generate anchor points along the frame with minimum distance constraint.

        Uses an efficient deterministic approach:
        1. Distribute points evenly around the frame
        2. Randomly displace each point while maintaining minimum distance to neighbors

        Args:
            frame_boundary: The frame boundary as a LineString
            frame_length: Total length of the frame boundary
            num_points: Number of anchor points to generate
            min_distance: Minimum distance between anchor points

        Returns:
            List of anchor point coordinates as (x, y) tuples
        """
        # Calculate even spacing between points
        even_spacing = frame_length / num_points

        # Check if minimum distance is achievable
        if even_spacing < min_distance:
            # Reduce number of points to make it achievable
            num_points = int(frame_length / min_distance)
            even_spacing = frame_length / num_points

        anchor_points: list[tuple[float, float]] = []

        # Generate evenly distributed points with random displacement
        for i in range(num_points):
            # Calculate even position along frame
            even_position = i * even_spacing

            # Calculate maximum displacement that maintains minimum distance
            # We can displace up to half the spacing minus half the minimum distance
            max_displacement = (even_spacing - min_distance) / 2

            # Apply random displacement
            if max_displacement > 0:
                displacement = random.uniform(-max_displacement, max_displacement)
            else:
                displacement = 0

            # Calculate final position
            position = even_position + displacement

            # Ensure position wraps around the frame boundary
            position = position % frame_length

            # Get point at this position
            point = frame_boundary.interpolate(position)
            anchor_points.append((point.x, point.y))

        return anchor_points

    def _select_layer_for_even_distribution(
        self, rods_by_layer: dict[int, list[Rod]], layer_targets: list[int]
    ) -> int:
        """
        Select a layer for the next rod to maintain even distribution.

        This method ensures that rods are distributed evenly across layers,
        with a maximum difference of 30% between the layer with the most rods
        and the layer with the fewest rods.

        Args:
            rods_by_layer: Dictionary mapping layer number to list of rods
            layer_targets: Target number of rods per layer

        Returns:
            Layer number (1-indexed) to assign the next rod to
        """
        # Find the layer with the fewest rods relative to its target
        min_layer = 1
        min_count = len(rods_by_layer[1])
        min_target = layer_targets[0]

        for layer_num in range(2, len(rods_by_layer) + 1):
            current_count = len(rods_by_layer[layer_num])
            current_target = layer_targets[layer_num - 1]

            # Prioritize layers that are furthest below their target
            if current_count < current_target:
                if min_count >= min_target or current_count < min_count:
                    min_layer = layer_num
                    min_count = current_count
                    min_target = current_target

        return min_layer
