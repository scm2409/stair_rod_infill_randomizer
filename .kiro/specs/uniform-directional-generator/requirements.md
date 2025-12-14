# Requirements Document

## Introduction

This document specifies the requirements for a Uniform Directional Generator, a deterministic infill generator that creates evenly distributed rod arrangements across configurable layers. Unlike the random generators (V1 and V2), this generator produces consistent, predictable patterns where each layer has a fixed main direction calculated from a configurable range. The generator prioritizes uniform distribution and visual consistency over randomness, making it ideal for production environments where reproducible results are required.

## Glossary

All terms from the base railing infill generator specification (`.kiro/specs/railing-infill-generator/requirements.md`) apply. Additional terms specific to this generator:

- **Uniform_Directional_Generator**: A deterministic infill generator that creates evenly distributed rods across configurable layers with fixed directional control
- **Layer_Main_Direction**: The fixed angle (relative to vertical) that all rods in a layer follow, calculated from the direction range
- **Main_Direction_Range**: The configurable minimum and maximum angles used to calculate layer main directions
- **Uniform_Distribution**: An arrangement where rods are evenly spaced along the frame boundary without random variation
- **Deterministic_Generation**: A generation process that produces identical results given the same input parameters
- **Anchor_Grid**: A pre-calculated set of evenly spaced anchor points along the frame boundary
- **Layer_Assignment_Pattern**: The systematic method of assigning anchor points to specific layers
- **Direct_Calculation**: Computing rod positions mathematically without iterative trial-and-error

## Base Requirements

All requirements from `.kiro/specs/railing-infill-generator/requirements.md` apply to the Uniform Directional Generator, including:
- Requirement 1: Rod arrangement generation (adapted for deterministic behavior)
- Requirement 6.1: Generator-specific parameters
- Requirement 7: UI integration
- Requirement 9.1.1: Progress metrics (simplified for non-iterative generation)

## Requirements

### Requirement 1

**User Story:** As a railing designer, I want a deterministic infill generator that produces consistent, evenly distributed rod patterns, so that I can create reproducible designs for production.

#### Acceptance Criteria

1. THE Uniform_Directional_Generator SHALL produce identical results when given the same input parameters and frame geometry
2. THE Uniform_Directional_Generator SHALL organize infill rods into a configurable number of layers
3. THE Uniform_Directional_Generator SHALL assign a distinct main direction angle to each layer based on the configured direction range
4. THE Uniform_Directional_Generator SHALL ensure all rods within a layer follow that layer's main direction exactly
5. THE Uniform_Directional_Generator SHALL distribute rods evenly across all layers

### Requirement 2

**User Story:** As a railing designer, I want to configure the number of layers and direction range, so that I can control the visual pattern of the infill.

#### Acceptance Criteria

1. THE Uniform_Directional_Generator SHALL accept a num_layers parameter specifying the number of rod layers
2. THE Uniform_Directional_Generator SHALL accept a main_direction_range_min_deg parameter for the minimum angle from vertical
3. THE Uniform_Directional_Generator SHALL accept a main_direction_range_max_deg parameter for the maximum angle from vertical
4. WHEN calculating layer main directions THEN the Uniform_Directional_Generator SHALL distribute directions evenly across the range using the formula: main_direction = min_angle + (layer_index / (num_layers - 1)) * (max_angle - min_angle)
5. WHEN there is only one layer THEN the Uniform_Directional_Generator SHALL use the midpoint of the direction range as the main direction
6. WHEN validating parameters THEN the Uniform_Directional_Generator SHALL ensure direction values are between -90 and 90 degrees
7. WHEN validating parameters THEN the Uniform_Directional_Generator SHALL ensure main_direction_range_min_deg is less than main_direction_range_max_deg
8. THE Uniform_Directional_Generator SHALL use default values of 3 layers with range -45° to +25°

### Requirement 3

**User Story:** As a railing designer, I want the generator to maintain minimum anchor spacing, so that rods are not placed too close together on the frame.

#### Acceptance Criteria

1. THE Uniform_Directional_Generator SHALL accept a min_anchor_distance_cm parameter for anchor spacing
2. THE Uniform_Directional_Generator SHALL ensure all anchor points are separated by at least min_anchor_distance_cm
3. THE Uniform_Directional_Generator SHALL enforce the minimum distance constraint globally across all anchor points regardless of layer
4. THE Uniform_Directional_Generator SHALL calculate anchor positions directly without iteration to satisfy the minimum distance constraint
5. WHEN the frame geometry cannot accommodate the requested number of rods with the minimum distance constraint THEN the Uniform_Directional_Generator SHALL fail with an error message

### Requirement 4

**User Story:** As a railing designer, I want to specify the number of rods to generate, so that I can control the density of the infill pattern.

#### Acceptance Criteria

1. THE Uniform_Directional_Generator SHALL accept a num_rods parameter specifying the total number of rods to generate
2. THE Uniform_Directional_Generator SHALL distribute the requested rods evenly across all layers
3. WHEN num_rods is not evenly divisible by num_layers THEN the Uniform_Directional_Generator SHALL assign extra rods to layers sequentially starting from layer 1

### Requirement 5

**User Story:** As a railing designer, I want the generator to use direct calculation instead of iteration, so that generation is fast and predictable.

#### Acceptance Criteria

1. THE Uniform_Directional_Generator SHALL calculate all anchor positions using direct mathematical computation
2. THE Uniform_Directional_Generator SHALL NOT use random number generation for anchor placement
3. THE Uniform_Directional_Generator SHALL NOT use iterative trial-and-error for rod placement
4. THE Uniform_Directional_Generator SHALL complete generation in a single pass through the anchor points
5. WHEN a rod cannot be placed at a calculated position due to constraints THEN the Uniform_Directional_Generator SHALL fail with an error message

### Requirement 6

**User Story:** As a railing designer, I want the generator to ensure rods do not cross within the same layer, so that the infill pattern is clean and manufacturable.

#### Acceptance Criteria

1. THE Uniform_Directional_Generator SHALL ensure rods within the same layer do not cross each other
2. THE Uniform_Directional_Generator SHALL allow rods in different layers to cross each other
3. THE Uniform_Directional_Generator SHALL ensure all rods remain completely within the frame boundary
4. THE Uniform_Directional_Generator SHALL anchor all rod endpoints to the frame boundary

### Requirement 7

**User Story:** As a railing designer, I want the generator to work with the existing evaluator system, so that I can assess the quality of generated patterns.

#### Acceptance Criteria

1. THE Uniform_Directional_Generator SHALL accept an evaluator parameter following the same pattern as RandomGeneratorV2
2. THE Uniform_Directional_Generator SHALL run the configured evaluator on the generated infill
3. THE Uniform_Directional_Generator SHALL include the fitness score in the returned RailingInfill
4. THE Uniform_Directional_Generator SHALL support both PassThroughEvaluator and QualityEvaluator

### Requirement 8

**User Story:** As a user, I want the generator integrated into the UI, so that I can select and configure it like other generators.

#### Acceptance Criteria

1. THE UI Application SHALL include "uniform_directional" as a selectable generator type
2. THE UI Application SHALL display parameter input fields for all Uniform_Directional_Generator parameters
3. THE UI Application SHALL load default parameter values from configuration files
4. THE UI Application SHALL validate parameter inputs using Pydantic validation

### Requirement 9

**User Story:** As a developer, I want the generator to follow existing patterns, so that it integrates seamlessly with the codebase.

#### Acceptance Criteria

1. THE Uniform_Directional_Generator SHALL extend the Generator base class
2. THE Uniform_Directional_Generator SHALL use UniformDirectionalGeneratorParameters as its PARAMETER_TYPE
3. THE Uniform_Directional_Generator SHALL emit progress_updated, best_result_updated, and generation_completed signals
4. THE Uniform_Directional_Generator SHALL be registered in the GeneratorFactory with key "uniform_directional"
5. THE Uniform_Directional_Generator SHALL store anchor points in the RailingInfill for visualization

