# Implementation Plan - RandomGenerator_v2

## Task Overview

This implementation plan creates RandomGenerator_v2, an enhanced random infill generator with layered directional control. The tasks build incrementally, starting with parameter models, then core generation logic, and finally UI integration and testing.

## Tasks

- [x] 1. Create parameter models and configuration
- [x] 1.1 Create RandomGeneratorDefaults_v2 dataclass
  - Define all v2-specific default values
  - Inherit from InfillGeneratorDefaults
  - _Requirements: 6.1.1-v2 (40-47)_

- [x] 1.2 Create RandomGeneratorParameters_v2 Pydantic model
  - Define all v2-specific parameters with validation
  - Inherit from InfillGeneratorParameters
  - Add field validators for direction range
  - Implement from_defaults() class method
  - _Requirements: 6.1.1-v2 (40-47)_

- [x] 1.3 Create Hydra configuration file
  - Create conf/generators/random_v2.yaml with default values
  - Register with Hydra ConfigStore
  - _Requirements: 6.1.1-v2 (40, 47)_

- [x]* 1.4 Write property test for parameter validation
  - **Property 1: Parameter validation correctness**
  - **Validates: Requirements 6.1.1-v2 (42-47)**
  - Test that invalid parameter combinations are rejected
  - Test that valid parameter combinations are accepted

- [x] 2. Implement frame segment classification
- [x] 2.1 Implement _classify_frame_segment() method
  - Calculate dx/dy ratio from frame rod geometry
  - Return True if vertical (dx/dy < 0.1), False otherwise
  - _Requirements: 6.1.1-v2 (4, 5, 6)_

- [ ]* 2.2 Write property test for frame segment classification
  - **Property 3: Frame segment classification correctness**
  - **Validates: Requirements 6.1.1-v2 (4, 5, 6)**
  - Generate random frame rods with known dx/dy ratios
  - Verify classification matches expected result based on threshold

- [x] 3. Implement anchor point generation
- [x] 3.1 Implement _generate_anchor_points_by_frame_segment() method
  - Iterate through frame rods
  - Classify each segment as vertical or other
  - Select appropriate min_distance parameter
  - Calculate number of anchors based on segment length
  - Distribute anchors evenly with random offsets
  - Use Shapely interpolate() for point coordinates
  - Log INFO with total anchor count
  - _Requirements: 6.1.1-v2 (1, 2, 3, 5, 7, 8, 60, 61)_

- [ ]* 3.2 Write property test for vertical anchor spacing
  - **Property 1: Anchor spacing on vertical frame segments**
  - **Validates: Requirements 6.1.1-v2 (2)**
  - Generate random vertical frame segments
  - Create anchor points
  - Verify all pairs separated by at least min_anchor_distance_vertical_cm

- [ ]* 3.3 Write property test for horizontal/sloped anchor spacing
  - **Property 2: Anchor spacing on horizontal/sloped frame segments**
  - **Validates: Requirements 6.1.1-v2 (3)**
  - Generate random horizontal/sloped frame segments
  - Create anchor points
  - Verify all pairs separated by at least min_anchor_distance_other_cm

- [x] 4. Implement anchor distribution to layers
- [x] 4.1 Implement _distribute_anchors_to_layers() method
  - Flatten all anchors from all segments
  - Randomize order with random.shuffle()
  - Distribute to layers using round-robin
  - Assign layer number to each anchor
  - Log INFO per layer with anchor count
  - _Requirements: 6.1.1-v2 (9, 10, 11, 12, 62)_

- [ ]* 4.2 Write property test for even anchor distribution
  - **Property 4: Even anchor distribution across layers**
  - **Validates: Requirements 6.1.1-v2 (10, 11, 12)**
  - Generate random number of anchors and layers
  - Distribute anchors
  - Verify difference between max and min layer sizes ≤ 1

- [x] 5. Implement layer main direction calculation
- [x] 5.1 Implement _calculate_layer_main_directions() method
  - Handle single layer case (use midpoint)
  - Handle multiple layers case (linear interpolation)
  - Use formula: min_angle + (layer_idx / (num_layers - 1)) * (max_angle - min_angle)
  - Log INFO per layer with main direction
  - _Requirements: 6.1.1-v2 (13, 14, 15, 16, 18, 19, 63)_

- [ ]* 5.2 Write property test for main direction distribution
  - **Property 5: Main direction even distribution**
  - **Validates: Requirements 6.1.1-v2 (15)**
  - Generate random number of layers and direction range
  - Calculate main directions
  - Verify even spacing across range

- [x] 6. Implement rod projection and anchor search
- [x] 6.1 Implement _project_and_find_end_anchor() method
  - Convert angle to radians
  - Calculate projection vector (dx, dy)
  - Create LineString extending in both positive and negative directions
  - Find intersection with frame boundary
  - Select intersection point on opposite side from start anchor
  - Search unused anchors for nearest to intersection
  - Return nearest anchor or None
  - _Requirements: 6.1.1-v2 (24, 25, 26, 27)_

- [ ]* 6.2 Write unit test for projection and search
  - Test with various angles and frame shapes
  - Verify correct intersection calculation
  - Verify nearest anchor selection
  - Test edge cases (no unused anchors, no intersection)

- [x] 7. Implement rod constraint validation
- [x] 7.1 Implement _validate_rod_constraints() method
  - Check length constraints (min and max)
  - Check boundary containment (Shapely within())
  - Check angle deviation from vertical
  - Check for same-layer crossings (Shapely crosses())
  - Update statistics counters for each failed check
  - Return True if all constraints met, False otherwise
  - _Requirements: 6.1.1-v2 (29, 30, 36, 37, 38, 39)_

- [ ]* 7.2 Write property test for constraint validation
  - **Property 9, 10, 11, 12: Base constraint compatibility**
  - **Validates: Requirements 6.1.1-v2 (36, 37, 38, 39)**
  - Generate random rods (valid and invalid)
  - Verify validation correctly identifies constraint violations

- [x] 8. Implement layer rod generation
- [x] 8.1 Implement _generate_layer_rods() method
  - Calculate target rod count for layer
  - Initialize empty rod list and unused anchor list
  - Iterate until target reached or limit exceeded
  - Select random start anchor
  - Calculate target angle (main direction + random offset)
  - Project and find end anchor
  - Create rod geometry
  - Validate constraints
  - Create Rod object if valid
  - Mark anchors as used
  - Log INFO at start with layer and main direction
  - Log INFO every 1000 iterations with progress
  - Log INFO or WARNING at completion
  - _Requirements: 6.1.1-v2 (20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 64, 65, 66)_

- [ ]* 8.2 Write property test for rod angle within deviation
  - **Property 6: Rod angle within deviation range**
  - **Validates: Requirements 6.1.1-v2 (21, 22)**
  - Generate random layers with main directions
  - Generate rods
  - Verify each rod's angle is within [main_direction - deviation, main_direction + deviation]

- [ ]* 8.3 Write property test for rod uses correct anchors
  - **Property 7: Rod uses correct anchor points**
  - **Validates: Requirements 6.1.1-v2 (23-30)**
  - Generate rods for a layer
  - Verify start and end points correspond to anchors from that layer
  - Verify both anchors marked as used

- [x] 9. Implement main generate() method
- [x] 9.1 Implement RandomGenerator_v2.generate() method
  - Validate parameter type
  - Reset cancellation flag and statistics
  - Execute Phase 1: Generate anchor points
  - Execute Phase 2: Distribute anchors to layers
  - Execute Phase 3: Calculate layer main directions
  - Execute Phase 4: Generate rods for each layer sequentially
  - Sum iterations across all layers
  - Check iteration and duration limits
  - Create RailingInfill result
  - Update statistics
  - Emit signals (progress_updated, best_result_updated, generation_completed)
  - Handle exceptions and emit generation_failed
  - Log INFO with final statistics
  - _Requirements: 6.1.1-v2 (31, 32, 33, 34, 35, 48, 49, 50, 51, 52, 55, 56, 57, 58, 59, 67)_

- [ ]* 9.2 Write property test for iteration sum
  - **Property 8: Total iterations sum across layers**
  - **Validates: Requirements 6.1.1-v2 (33, 34)**
  - Generate infill with multiple layers
  - Track iterations per layer
  - Verify total equals sum of layer iterations

- [ ]* 9.3 Write property test for statistics accuracy
  - **Property 13: Statistics accuracy**
  - **Validates: Requirements 6.1.1-v2 (59)**
  - Generate infill
  - Verify statistics match actual rods created, iterations used, duration

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise

- [x] 11. Create UI parameter widget
- [x] 11.1 Create RandomGeneratorParameterWidget_v2 class
  - Inherit from QWidget
  - Create input fields for all v2 parameters
  - Use QDoubleSpinBox with appropriate ranges and units
  - Implement get_parameters() method
  - Display Pydantic validation errors with red highlighting
  - _Requirements: 6.1.1-v2 (41, 42, 43, 44, 45, 46)_

- [ ]* 11.2 Write integration test for parameter widget
  - Test widget creation with defaults
  - Test get_parameters() returns correct values
  - Test validation error display

- [x] 12. Register generator in factory
- [x] 12.1 Add RandomGenerator_v2 to generator factory registry
  - Register with key "random_v2"
  - Update factory to create RandomGenerator_v2 instances
  - _Requirements: 6.1.1-v2 (UI integration)_

- [ ]* 12.2 Write integration test for factory registration
  - Test factory creates RandomGenerator_v2 for "random_v2" key
  - Test generator has correct PARAMETER_TYPE

- [x] 13. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise
