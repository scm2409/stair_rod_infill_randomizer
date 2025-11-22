# Design Document - RandomGenerator_v2

## Overview

RandomGenerator_v2 is an enhanced random infill generator that improves upon the original RandomGenerator through a layered directional approach. The key innovation is pre-generating anchor points with frame-segment-specific spacing constraints, organizing them into layers, and assigning each layer a main direction with controlled variation. This approach provides better visual structure, more efficient generation, and maintains all compatibility with the existing system.

**This design extends the base railing infill generator design (`.kiro/specs/railing-infill-generator/design.md`) with v2-specific enhancements.**

## Key Improvements Over RandomGenerator

1. **Frame-Aware Anchor Spacing**: Different minimum distances for vertical frame rods (posts) vs horizontal/sloped frame rods (handrails)
2. **Pre-Generation Strategy**: All anchor points created upfront, then distributed to layers
3. **Directional Control**: Each layer has a main direction with configurable variation
4. **Efficient Rod Creation**: Project from anchor point at target angle, find nearest anchor on opposite side
5. **Layer-Based Iteration**: Independent iteration tracking per layer for better debugging and future parallelization

## Architecture

RandomGenerator_v2 implements the existing `Generator` interface and follows the same layered architecture as the base system. The generator receives a `RailingFrame` and `RandomGeneratorParameters_v2`, then produces a `RailingInfill` result.

### High-Level Flow

```
Input: RailingFrame + RandomGeneratorParameters_v2
    ↓
Phase 1: Generate anchor points (frame-segment-aware spacing)
    ↓
Phase 2: Distribute anchors to layers (randomized, even distribution)
    ↓
Phase 3: Calculate layer main directions (evenly spaced across range)
    ↓
Phase 4: Generate rods per layer (project-and-search approach)
    ↓
Output: RailingInfill
```

## Components and Interfaces

### 1. RandomGeneratorParameters_v2

Pydantic model extending `InfillGeneratorParameters` with v2-specific fields:

**Inherited Parameters** (from RandomGeneratorParameters):
- `num_rods`: Number of infill rods to generate
- `min_rod_length_cm`, `max_rod_length_cm`: Rod length constraints
- `max_angle_deviation_deg`: Maximum angle from vertical
- `num_layers`: Number of rod layers
- `max_iterations`, `max_duration_sec`: Generation limits
- `infill_weight_per_meter_kg_m`: Rod weight for BOM calculations

**New V2 Parameters**:
- `min_anchor_distance_vertical_cm`: Minimum spacing for anchors on vertical frame rods (e.g., posts)
- `min_anchor_distance_other_cm`: Minimum spacing for anchors on horizontal/sloped frame rods (e.g., handrails)
- `main_direction_range_min_deg`: Minimum angle for layer main directions (degrees from vertical)
- `main_direction_range_max_deg`: Maximum angle for layer main directions (degrees from vertical)
- `random_angle_deviation_deg`: Random deviation from layer main direction (±degrees)

**Validation Rules**:
- All distance parameters must be > 0
- Direction range min/max must be in [-90, 90]
- Direction range max must be > min
- Random deviation must be ≥ 0

### 2. RandomGeneratorDefaults_v2

Hydra dataclass for configuration defaults:

**Default Values**:
- Base parameters: Same as RandomGenerator (50 rods, 2 layers, 1000 iterations, etc.)
- `min_anchor_distance_vertical_cm`: 15.0 cm (sparser on vertical posts)
- `min_anchor_distance_other_cm`: 5.0 cm (denser on handrails)
- `main_direction_range_min_deg`: -30.0°
- `main_direction_range_max_deg`: +30.0°
- `random_angle_deviation_deg`: 30.0°

### 3. RandomGenerator_v2 Class

Implements the `Generator` interface with the following key methods:

**Public Interface**:
- `generate(frame, params) -> RailingInfill`: Main generation method
- `get_statistics() -> GenerationStatistics`: Returns generation metrics
- Inherits signal emissions: `progress_updated`, `best_result_updated`, `generation_completed`, `generation_failed`

**Private Helper Methods**:
- `_generate_anchor_points_by_frame_segment()`: Creates anchors with frame-aware spacing
- `_classify_frame_segment()`: Determines if frame rod is vertical or not
- `_distribute_anchors_to_layers()`: Randomizes and evenly distributes anchors
- `_calculate_layer_main_directions()`: Computes evenly-spaced main directions
- `_generate_layer_rods()`: Generates rods for a single layer
- `_project_and_find_end_anchor()`: Projects line and finds nearest anchor
- `_validate_rod_constraints()`: Checks length, boundary, crossings

## Data Models

### AnchorPoint (Internal)

Represents an anchor point on the frame boundary with the following attributes:
- Position (x, y coordinates)
- Frame segment index (which frame rod it's on)
- Vertical segment flag (True if on vertical frame rod)
- Assigned layer (1-N, or None if unassigned)
- Used flag (True if already used in a rod)

### LayerGenerationResult (Internal)

Encapsulates the result of generating rods for a single layer:
- List of generated rods
- Number of iterations used
- Success/failure status
- Optional failure reason

## Algorithm Overview

### Phase 1: Generate Anchor Points by Frame Segment

**Purpose**: Create anchor points along the frame boundary with appropriate spacing based on frame segment orientation.

**Approach**:
1. Iterate through each frame rod (segment)
2. Classify segment as vertical or horizontal/sloped based on dx/dy ratio (threshold: 0.1)
3. Select appropriate minimum distance parameter based on classification
4. Calculate number of anchors: `segment_length / min_distance`
5. Distribute anchors evenly along segment with random offsets (±50% of min_distance)
6. Use Shapely's `interpolate()` to get point coordinates at each position
7. Store anchors grouped by frame segment index

**Logging**: INFO message with total anchor count and segment count

### Phase 2: Distribute Anchors to Layers

**Purpose**: Evenly distribute anchor points across layers with randomization.

**Approach**:
1. Flatten all anchors from all segments into single list
2. Randomize order using `random.shuffle()`
3. Distribute to layers using round-robin: `layer = (index % num_layers) + 1`
4. Assign layer number to each anchor point
5. Result: Each layer has approximately equal number of anchors (difference ≤ 1)

**Logging**: INFO message per layer with anchor count

### Phase 3: Calculate Layer Main Directions

**Purpose**: Assign each layer a main direction angle evenly distributed across the configured range.

**Approach**:
1. **Single layer**: Use midpoint of range: `(min + max) / 2`
2. **Multiple layers**: Linear interpolation across range
   - For layer index i (0-based): `t = i / (num_layers - 1)`
   - Main direction: `min_angle + t * (max_angle - min_angle)`
3. Example with 3 layers and range [-30°, +30°]:
   - Layer 1: -30°
   - Layer 2: 0°
   - Layer 3: +30°

**Logging**: INFO message per layer with main direction angle

### Phase 4: Generate Layer Rods

**Purpose**: Generate rods for a single layer using the projection-and-search approach.

**Approach**:
1. Calculate target rod count for this layer (evenly distributed with remainder handling)
2. Initialize empty rod list and unused anchor list
3. Iterate until target reached or iteration limit:
   a. Select random unused anchor as start point
   b. Calculate target angle: `main_direction + random_offset` where offset ∈ [-deviation, +deviation]
   c. Project line from start point at target angle
   d. Find intersection with frame boundary using Shapely
   e. Find nearest unused anchor to intersection point
   f. Create rod geometry connecting start and end anchors
   g. Validate constraints (length, boundary, no same-layer crossings)
   h. If valid: create Rod, mark anchors as used, add to layer rods
   i. If invalid: continue to next iteration
4. Return generated rods and iteration count

**Logging**: 
- INFO at start with layer number and main direction
- INFO every 1000 iterations with progress
- INFO or WARNING at completion with rod count and iterations

### Helper: Project and Find End Anchor

**Purpose**: Project a line from start anchor at target angle and find nearest unused anchor.

**Approach**:
1. Convert angle to radians (0° = vertical, positive = clockwise)
2. Calculate projection vector: `dx = length * sin(angle)`, `dy = length * cos(angle)`
3. Create LineString extending in **both directions** from start point:
   - Positive direction: `(start_x + dx, start_y + dy)`
   - Negative direction: `(start_x - dx, start_y - dy)`
   - This ensures the line will intersect the frame boundary regardless of start anchor position
4. Find intersection with frame boundary using Shapely's `intersection()`
5. Select the intersection point that is **not** near the start anchor (the opposite side)
6. Search all unused anchors for nearest to the selected intersection point
7. Return nearest anchor or None if not found

### Helper: Validate Rod Constraints

**Purpose**: Check if a rod meets all constraints.

**Checks**:
1. Length: `min_rod_length_cm ≤ length ≤ max_rod_length_cm`
2. Boundary: Rod geometry completely within frame boundary (Shapely's `within()`)
3. Angle: Actual angle ≤ `max_angle_deviation_deg` (calculated from dx/dy)
4. Same-layer crossings: No crossings with existing rods in same layer (Shapely's `crosses()`)

**Statistics**: Increment appropriate counter for each failed check

### Helper: Classify Frame Segment

**Purpose**: Determine if a frame rod is vertical or horizontal/sloped.

**Approach**:
- Calculate dx and dy from rod endpoints
- If `dy > 0` and `dx / dy < 0.1`: classify as vertical
- Otherwise: classify as horizontal/sloped
- Threshold of 0.1 means up to 10% horizontal displacement is considered "vertical"

## Error Handling

### Validation Errors

- **Parameter validation**: Pydantic raises `ValidationError` with detailed field-level errors
- **UI handling**: Display validation errors in parameter panels with red highlighting
- **Configuration errors**: Log and use fallback defaults if config file is invalid

### Generation Failures

- **Insufficient anchors**: Log warning and return partial result
- **Iteration limit**: Return best result found so far
- **Duration limit**: Return best result found so far
- **Layer failure**: Log which layer failed and continue with other layers
- **Cancellation**: Emit `generation_failed` signal with cancellation message

### Logging Strategy

All significant events are logged at appropriate levels:
- **INFO**: Phase starts/completions, anchor counts, layer progress every 1000 iterations
- **WARNING**: Layer failures, insufficient anchors
- **ERROR**: Unexpected exceptions, validation failures
- **DEBUG**: Detailed iteration information (if enabled)

## Testing Strategy

### Unit Tests

Test individual methods in isolation:

1. **Anchor Point Generation**:
   - Test `_generate_anchor_points_by_frame_segment()` with various frame configurations
   - Verify correct spacing for vertical vs horizontal segments
   - Test edge cases (very short segments, single-rod frames)

2. **Frame Segment Classification**:
   - Test `_classify_frame_segment()` with vertical, horizontal, and angled rods
   - Verify threshold behavior (dx/dy < 0.1)

3. **Layer Distribution**:
   - Test `_distribute_anchors_to_layers()` with various anchor counts and layer counts
   - Verify even distribution and randomization

4. **Main Direction Calculation**:
   - Test `_calculate_layer_main_directions()` with 1, 2, 3, and 5 layers
   - Verify correct interpolation across range

5. **Projection and Search**:
   - Test `_project_and_find_end_anchor()` with various angles and frame shapes
   - Verify correct intersection calculation and nearest-anchor selection

6. **Constraint Validation**:
   - Test `_validate_rod_constraints()` with valid and invalid rods
   - Verify all constraint checks (length, boundary, crossings, angle)

### Property-Based Tests

Property-based tests verify universal properties across many random inputs using Hypothesis.


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Anchor Spacing on Vertical Frame Segments

*For any* vertical frame segment and generated anchor points on that segment, all pairs of anchor points should be separated by at least min_anchor_distance_vertical_cm.

**Validates: Requirements 2**

### Property 2: Anchor Spacing on Horizontal/Sloped Frame Segments

*For any* horizontal or sloped frame segment and generated anchor points on that segment, all pairs of anchor points should be separated by at least min_anchor_distance_other_cm.

**Validates: Requirements 3**

### Property 3: Frame Segment Classification Correctness

*For any* frame rod, if its horizontal displacement (dx) divided by its vertical displacement (dy) is less than 0.1, it should be classified as vertical; otherwise it should be classified as horizontal/sloped.

**Validates: Requirements 4, 5, 6**

### Property 4: Even Anchor Distribution Across Layers

*For any* set of anchor points distributed across N layers, the difference between the layer with the most anchors and the layer with the fewest anchors should be at most 1.

**Validates: Requirements 10, 11, 12**

### Property 5: Main Direction Even Distribution

*For any* number of layers N ≥ 2 and direction range [min_deg, max_deg], the main directions assigned to layers should be evenly spaced across the range, with the spacing equal to (max_deg - min_deg) / (N - 1).

**Validates: Requirements 15**

### Property 6: Rod Angle Within Deviation Range

*For any* generated rod in a layer with main direction M and random deviation D, the rod's actual angle should be within the range [M - D, M + D] (allowing for small numerical tolerance).

**Validates: Requirements 21, 22**

### Property 7: Rod Uses Correct Anchor Points

*For any* generated rod, both its start and end points should correspond to anchor points from the rod's assigned layer, and both anchor points should be marked as used.

**Validates: Requirements 23, 24, 25, 26, 27, 28, 29, 30**

### Property 8: Total Iterations Sum Across Layers

*For any* generation run with multiple layers, the total iteration count reported in the statistics should equal the sum of iterations used by each individual layer.

**Validates: Requirements 33, 34**

### Property 9: Base Constraint Compatibility - Rod Length

*For any* generated rod, its length should be between min_rod_length_cm and max_rod_length_cm (inclusive).

**Validates: Requirements 36**

### Property 10: Base Constraint Compatibility - Boundary Containment

*For any* generated rod, its geometry should be completely within the frame boundary polygon.

**Validates: Requirements 37**

### Property 11: Base Constraint Compatibility - No Same-Layer Crossings

*For any* two rods in the same layer, their geometries should not cross each other (they may touch at endpoints but not intersect).

**Validates: Requirements 38**

### Property 12: Base Constraint Compatibility - Frame Anchoring

*For any* generated rod, both its start and end points should lie on the frame boundary (within a small tolerance for numerical precision).

**Validates: Requirements 39**

### Property 13: Statistics Accuracy

*For any* completed generation run, the statistics should accurately reflect the number of rods created, iterations used, and duration elapsed.

**Validates: Requirements 59**

## Configuration Files

### Hydra Configuration

Create `conf/generators/random_v2.yaml` with default values for all parameters:
- Base parameters (inherited from RandomGenerator)
- V2-specific parameters with defaults as specified in RandomGeneratorDefaults_v2

Register with Hydra ConfigStore:
- Group: "generators"
- Name: "random_v2"
- Node: RandomGeneratorDefaults_v2 dataclass

## UI Integration

### Parameter Panel

Create `RandomGeneratorParameterWidget_v2` extending the existing parameter widget pattern:

**Input Fields** (QDoubleSpinBox with appropriate ranges and units):
- All base parameters (inherited from RandomGenerator widget)
- Min Anchor Distance (Vertical): 0.1-100.0 cm
- Min Anchor Distance (Other): 0.1-100.0 cm
- Main Direction Min: -90.0 to 90.0 degrees
- Main Direction Max: -90.0 to 90.0 degrees
- Random Angle Deviation: 0.0 to 90.0 degrees

**Methods**:
- `get_parameters()`: Extract values and create RandomGeneratorParameters_v2 instance
- Pydantic validation errors displayed with red highlighting

### Generator Factory

Register RandomGenerator_v2 in the generator factory registry:
- Key: "random_v2"
- Value: RandomGenerator_v2 class
- Factory creates instance when "random_v2" type is selected in UI

## Performance Considerations

### Expected Performance

- **Anchor generation**: O(N) where N is total frame perimeter / min_distance
- **Layer distribution**: O(N) for shuffling and assignment
- **Rod generation per layer**: O(M * A) where M is target rods and A is available anchors
- **Overall complexity**: O(L * M * A) where L is layers, M is rods per layer, A is anchors per layer

### Optimization Opportunities

1. **Spatial indexing**: Use STRtree for faster nearest-anchor search
2. **Parallel layer generation**: Process layers in parallel (future enhancement)
3. **Early termination**: Stop layer iteration when anchor pool is exhausted
4. **Anchor pool management**: Use set for O(1) used-anchor lookups

### Memory Usage

- **Anchor points**: ~100-500 points × 64 bytes = 6-32 KB
- **Rods**: ~50-200 rods × 256 bytes = 13-51 KB
- **Total**: < 100 KB for typical cases

## Migration from RandomGenerator

### Backward Compatibility

RandomGenerator_v2 is a separate generator type and does not replace RandomGenerator. Both can coexist:

- **RandomGenerator**: Original algorithm, single min_anchor_distance parameter
- **RandomGenerator_v2**: Enhanced algorithm, separate vertical/other distances, layered directions

### Parameter Migration

Users can migrate from RandomGenerator to RandomGenerator_v2 by:

1. Setting `min_anchor_distance_vertical_cm = min_anchor_distance_cm`
2. Setting `min_anchor_distance_other_cm = min_anchor_distance_cm`
3. Setting `main_direction_range_min_deg = -max_angle_deviation_deg`
4. Setting `main_direction_range_max_deg = max_angle_deviation_deg`
5. Setting `random_angle_deviation_deg = max_angle_deviation_deg`

This configuration approximates the original behavior while enabling the new features.

## Future Enhancements

### Parallel Layer Generation

The layer-based architecture enables future parallelization:

```python
from concurrent.futures import ThreadPoolExecutor

def generate_parallel(self, frame, params):
    """Generate all layers in parallel."""
    with ThreadPoolExecutor(max_workers=params.num_layers) as executor:
        futures = [
            executor.submit(
                self._generate_layer_rods,
                layer_num=layer,
                available_anchors=anchors_by_layer[layer],
                main_direction=layer_main_directions[layer],
                frame=frame,
                params=params,
                existing_rods=[]  # No cross-layer checking in parallel mode
            )
            for layer in range(1, params.num_layers + 1)
        ]
        
        results = [future.result() for future in futures]
```

### Adaptive Anchor Density

Dynamically adjust anchor density based on frame segment length and curvature:

```python
def _calculate_adaptive_anchor_count(
    self,
    segment_length: float,
    segment_curvature: float,
    base_min_distance: float
) -> int:
    """Calculate anchor count based on segment characteristics."""
    # More anchors on curved segments
    curvature_factor = 1.0 + segment_curvature * 0.5
    adjusted_distance = base_min_distance / curvature_factor
    return max(int(segment_length / adjusted_distance), 2)
```

### Quality Evaluation Integration

Add optional fitness evaluation to v2 for quality-driven generation:

```python
def generate_with_quality(self, frame, params, evaluator):
    """Generate with quality evaluation (optional)."""
    best_infill = None
    best_fitness = float('-inf')
    
    for attempt in range(params.max_attempts):
        infill = self.generate(frame, params)
        fitness = evaluator.evaluate(infill, frame)
        
        if fitness > best_fitness:
            best_fitness = fitness
            best_infill = infill
    
    return best_infill
```

## Summary

RandomGenerator_v2 enhances the original random generator with:

1. **Frame-aware anchor spacing**: Different densities for vertical vs horizontal frame segments
2. **Layered directional control**: Each layer has a main direction with controlled variation
3. **Efficient rod generation**: Project-and-search approach for faster convergence
4. **Better debugging**: Layer-based iteration tracking and comprehensive logging
5. **Future-ready**: Architecture supports parallelization and quality evaluation

The design maintains full compatibility with the existing system while providing significant improvements in efficiency, visual structure, and maintainability.
