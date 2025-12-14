# Implementation Plan

## Task Overview

This implementation plan creates the Uniform Directional Generator, a deterministic infill generator with evenly distributed rods across configurable layers. The tasks build incrementally, starting with parameter models, then core generation logic, and finally UI integration.

## Tasks

- [x] 1. Create parameter models and configuration
  - [x] 1.1 Create UniformDirectionalGeneratorDefaults dataclass
    - Define all default values (num_rods=30, num_layers=3, etc.)
    - Inherit from InfillGeneratorDefaults
    - Register with Hydra ConfigStore
    - _Requirements: 2.1, 2.2, 2.3, 2.8_

  - [x] 1.2 Create UniformDirectionalGeneratorParameters Pydantic model
    - Define all parameters with validation (num_rods, num_layers, direction range, min_anchor_distance_cm, evaluator)
    - Inherit from InfillGeneratorParameters
    - Add model_validator for direction range (min < max)
    - Implement from_defaults() class method
    - _Requirements: 2.1, 2.2, 2.3, 2.6, 2.7, 3.1, 4.1_

  - [x] 1.3 Create Hydra configuration file
    - Create conf/generators/uniform_directional.yaml with default values
    - _Requirements: 8.3_

  - [x] 1.4 Write property test for parameter validation
    - **Property 7: Parameter Validation**
    - **Validates: Requirements 2.6, 2.7**
    - Test that invalid direction ranges are rejected
    - Test that valid parameters are accepted

- [x] 2. Implement anchor grid generation
  - [x] 2.1 Implement _generate_anchor_grid() method
    - Calculate frame perimeter
    - Calculate maximum anchors based on min_anchor_distance_cm
    - Place anchors at uniform intervals using Shapely interpolate()
    - Return list of AnchorPoint objects (all marked as free)
    - _Requirements: 3.1, 3.2, 3.4_

  - [x] 2.2 Write property test for minimum anchor distance
    - **Property 4: Minimum Anchor Distance**
    - **Validates: Requirements 3.2, 3.3**
    - Generate anchor grid for random frames
    - Verify all anchor pairs are at least min_anchor_distance_cm apart

- [x] 3. Implement layer direction calculation
  - [x] 3.1 Implement _calculate_layer_directions() method
    - Handle single layer case (midpoint)
    - Handle multiple layers (linear interpolation)
    - Return dict mapping layer number to direction angle
    - _Requirements: 2.4, 2.5_

  - [x] 3.2 Write property test for layer direction calculation
    - **Property 3: Layer Direction Calculation**
    - **Validates: Requirements 1.3, 1.4, 2.4, 2.5**
    - Test direction formula for various layer counts and ranges

- [x] 4. Implement line pattern generation
  - [x] 4.1 Implement _generate_line_pattern() method
    - Calculate frame bounding box
    - Generate parallel lines at layer's direction angle
    - Space lines evenly to achieve target rod count
    - Return list of LineString objects
    - _Requirements: 1.4, 5.1_

  - [x] 4.2 Implement _find_boundary_intersections() method
    - Find intersections of each line with frame boundary
    - Return list of intersection point pairs
    - _Requirements: 6.3_

  - [x] 4.3 Implement _snap_to_nearest_anchor() method
    - Find nearest free anchor to intersection point
    - Return anchor or None if no suitable anchor found
    - _Requirements: 3.2, 6.4_

- [x] 5. Implement rod generation
  - [x] 5.1 Implement _generate_layer_rods() method
    - Generate line pattern for layer
    - Find boundary intersections
    - Snap intersections to free anchors
    - Create rods connecting anchor pairs
    - Mark anchors as used
    - Skip lines where anchors not found
    - _Requirements: 1.4, 5.4, 6.4_

  - [x] 5.2 Write property test for rod constraint satisfaction
    - **Property 5: Rod Constraint Satisfaction**
    - **Validates: Requirements 6.1, 6.3, 6.4**
    - Verify no same-layer crossings
    - Verify rods within boundary
    - Verify endpoints on boundary

- [x] 6. Implement main generate() method
  - [x] 6.1 Implement UniformDirectionalGenerator.generate() method
    - Validate parameter type
    - Create evaluator from nested parameters
    - Execute Phase 1: Generate anchor grid
    - Execute Phase 2: Calculate layer directions
    - Execute Phase 3-4: Generate rods for each layer
    - Verify rod count matches requested (fail if insufficient)
    - Run evaluator and set fitness score
    - Emit signals (progress_updated, generation_completed)
    - Create and return RailingInfill
    - _Requirements: 1.1, 1.2, 1.5, 4.2, 4.3, 7.1, 7.2, 7.3, 9.3_

  - [x] 6.2 Write property test for deterministic generation
    - **Property 1: Deterministic Generation**
    - **Validates: Requirements 1.1, 5.2**
    - Generate infill twice with same inputs
    - Verify identical results

  - [x] 6.3 Write property test for even layer distribution
    - **Property 2: Even Layer Distribution**
    - **Validates: Requirements 1.2, 1.5, 4.2, 4.3**
    - Verify rod count difference between layers is at most 1

  - [x] 6.4 Write property test for fail-fast behavior
    - **Property 6: Fail-Fast on Constraint Violation**
    - **Validates: Requirements 3.5, 5.5**
    - Test with parameters that cannot be satisfied
    - Verify RuntimeError is raised

  - [x] 6.5 Write property test for evaluator integration
    - **Property 8: Evaluator Integration**
    - **Validates: Requirements 7.2, 7.3**
    - Verify fitness_score is populated in result

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Create UI parameter widget
  - [x] 8.1 Create UniformDirectionalGeneratorParameterWidget class
    - Inherit from GeneratorParameterWidget
    - Create input fields for all parameters
    - Implement get_parameters() method
    - Include nested evaluator widget
    - _Requirements: 8.1, 8.2, 8.4_

- [x] 9. Register generator in factory
  - [x] 9.1 Add UniformDirectionalGenerator to generator factory registry
    - Register with key "uniform_directional"
    - Update factory to create instances
    - _Requirements: 9.1, 9.4_

  - [x] 9.2 Add generator to UI dropdown
    - Add "uniform_directional" option to generator type selector
    - Connect to parameter widget switching
    - _Requirements: 8.1_

- [ ] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

