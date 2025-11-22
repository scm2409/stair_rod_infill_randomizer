"""Random infill generator implementation."""
import random
import time

from shapely.geometry import LineString

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


class RandomGenerator(Generator):
    """
    Random infill generator with simple random placement.

    This is a simplified version without quality evaluation.
    It generates random rod arrangements that respect basic constraints:
    - Rods within same layer do not cross
    - Rods remain within frame boundary
    - Rods are anchored to the frame
    """

    def generate(
        self, frame: RailingFrame, params: InfillGeneratorParameters
    ) -> RailingInfill:
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

        # Reset cancellation flag
        self.reset_cancellation()

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

                    # For now, accept the first valid arrangement
                    # (quality evaluation will be added in Task 6)
                    self.generation_completed.emit(infill)
                    return infill

                except ValueError:
                    # Failed to generate valid arrangement, try again
                    continue

            # Max iterations reached without valid result
            if best_infill is not None:
                self.generation_completed.emit(best_infill)
                return best_infill

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
        rods: list[Rod] = []

        # Get frame boundary as LineString for anchor point selection
        frame_boundary = LineString(frame.boundary.exterior.coords)
        frame_length = frame_boundary.length

        # Organize rods by layer
        rods_by_layer: dict[int, list[Rod]] = {
            layer: [] for layer in range(1, params.num_layers + 1)
        }

        # Generate rods
        for _ in range(params.num_rods):
            # Randomly assign to a layer
            layer = random.randint(1, params.num_layers)

            # Try to create a valid rod
            max_attempts = 50
            for _ in range(max_attempts):
                # Select random anchor points on frame
                anchor1_distance = random.uniform(0, frame_length)
                anchor1 = frame_boundary.interpolate(anchor1_distance)

                # Select second anchor with minimum distance constraint
                anchor2_distance = random.uniform(0, frame_length)
                # Check minimum distance
                if abs(anchor2_distance - anchor1_distance) < params.min_anchor_distance_cm:
                    continue

                anchor2 = frame_boundary.interpolate(anchor2_distance)

                # Create rod geometry
                rod_geometry = LineString([anchor1.coords[0], anchor2.coords[0]])

                # Check length constraint
                if rod_geometry.length > params.max_rod_length_cm:
                    continue

                # Check if rod is within boundary
                if not frame.boundary.contains(rod_geometry):
                    # Allow if rod is on the boundary
                    if not frame.boundary.touches(rod_geometry):
                        continue

                # Check angle deviation from vertical
                dx = anchor2.x - anchor1.x
                dy = anchor2.y - anchor1.y
                if dx == 0:
                    angle_deg = 0.0  # Perfectly vertical
                else:
                    import math

                    angle_rad = math.atan(abs(dx) / abs(dy)) if dy != 0 else math.pi / 2
                    angle_deg = math.degrees(angle_rad)

                if angle_deg > params.max_angle_deviation_deg:
                    continue

                # Check for crossings with same-layer rods
                crosses_same_layer = False
                for existing_rod in rods_by_layer[layer]:
                    if rod_geometry.crosses(existing_rod.geometry):
                        crosses_same_layer = True
                        break

                if crosses_same_layer:
                    continue

                # Create rod
                rod = Rod(
                    geometry=rod_geometry,
                    start_cut_angle_deg=0.0,  # Simplified: no cut angles yet
                    end_cut_angle_deg=0.0,
                    weight_kg_m=params.infill_weight_per_meter_kg_m,
                    layer=layer,
                )

                # Add to layer and overall list
                rods_by_layer[layer].append(rod)
                rods.append(rod)
                break

        # Check if we generated enough rods
        if len(rods) < params.num_rods * 0.5:  # At least 50% of requested rods
            raise ValueError(
                f"Only generated {len(rods)} rods out of {params.num_rods} requested"
            )

        return rods
