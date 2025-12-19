# Requirements Document: Evolutionary Infill Generator

## Introduction

This document specifies the requirements for the Evolutionary Infill Generator, a hybrid generator that combines the structured initial generation approach of the Uniform Directional Generator with iterative random modifications and fitness-based selection. Instead of generating random infill from scratch each iteration, this generator starts with a deterministic uniform baseline and then applies random mutations, keeping improvements that increase the fitness score.

The key innovation is the evolutionary optimization loop: generate a structured baseline, apply random modifications, evaluate fitness, and keep the modification only if it improves the score. This approach converges toward better solutions without restarting from scratch.

## Glossary

- **Evolutionary_Infill_Generator**: The hybrid generator combining uniform baseline generation with iterative mutation and selection
- **Baseline_Infill**: The initial deterministic infill arrangement generated using uniform directional logic
- **Mutation**: A random modification applied to rod endpoints by shifting them to neighboring anchor points along the frame boundary
- **Fitness_Score**: A numerical score (0.0-1.0) calculated by the evaluator indicating arrangement quality
- **Selection**: The process of keeping or discarding a mutation based on fitness comparison
- **Iteration**: One cycle of mutation (all layers), evaluation, and selection
- **Improvement_Threshold**: Minimum fitness increase required to accept a mutation (prevents accepting negligible improvements)
- **Stagnation**: When no improvements are found for a specified number of consecutive iterations
- **Stagnation_Limit**: The number of consecutive iterations without improvement that triggers early termination
- **Rod_Mutation**: Modification of a single rod by moving its endpoints to neighboring free anchor points along the frame
- **Anchor_Pool**: The set of all anchor points generated once at baseline creation; each anchor is either free or used
- **Free_Anchor**: An anchor point not currently connected to any rod, available for use
- **Used_Anchor**: An anchor point currently connected to a rod, assigned to that rod's layer
- **Next_Free_Anchor**: The nearest free anchor point along the frame boundary in a given direction (clockwise or counterclockwise)

## Requirements

### Requirement 1: Baseline Generation

**User Story:** As a user, I want the generator to start with a structured uniform baseline, so that the optimization begins from a reasonable starting point rather than random chaos.

#### Acceptance Criteria

1. WHEN generation starts THEN the Evolutionary_Infill_Generator SHALL create an initial baseline infill using uniform directional generation logic
2. WHEN creating the baseline THEN the Evolutionary_Infill_Generator SHALL distribute rods evenly across configured layers
3. WHEN creating the baseline THEN the Evolutionary_Infill_Generator SHALL assign each layer a main direction angle using linear interpolation across the configured direction range
4. WHEN the baseline is created THEN the Evolutionary_Infill_Generator SHALL evaluate its fitness score using the configured evaluator
5. WHEN the baseline is created THEN the Evolutionary_Infill_Generator SHALL emit a best_result_updated signal with the baseline infill

### Requirement 2: Anchor Point Management

**User Story:** As a user, I want anchor points to be generated once and reused throughout the optimization, so that the mutation process is efficient and consistent.

#### Acceptance Criteria

1. WHEN generation starts THEN the Evolutionary_Infill_Generator SHALL generate all anchor points once during baseline creation
2. THE Evolutionary_Infill_Generator SHALL NOT regenerate anchor points during mutation iterations
3. WHEN a rod is disconnected from an anchor point THEN the Evolutionary_Infill_Generator SHALL mark that anchor point as free (available for reuse)
4. WHEN a rod is disconnected from an anchor point THEN the Evolutionary_Infill_Generator SHALL clear the layer assignment of that anchor point
5. WHEN connecting a rod to an anchor point THEN the Evolutionary_Infill_Generator SHALL mark that anchor point as used and assign it to the rod's layer

### Requirement 3: Mutation Operations

**User Story:** As a user, I want the generator to apply random modifications by shifting rod endpoints to nearby anchor points, so that the solution can explore neighboring configurations.

#### Acceptance Criteria

1. WHEN performing a mutation iteration THEN the Evolutionary_Infill_Generator SHALL process each layer sequentially
2. WHEN mutating a rod THEN the Evolutionary_Infill_Generator SHALL attempt to move each endpoint to the next free anchor point along the frame boundary
3. WHEN selecting the next anchor point THEN the Evolutionary_Infill_Generator SHALL search along the frame boundary in a random direction (clockwise or counterclockwise)
4. WHEN a rod endpoint is moved THEN the Evolutionary_Infill_Generator SHALL release the original anchor point (mark as free, clear layer)
5. WHEN a rod endpoint is moved THEN the Evolutionary_Infill_Generator SHALL claim the new anchor point (mark as used, assign layer)
6. WHEN a mutated rod intersects with another rod in the same layer THEN the Evolutionary_Infill_Generator SHALL undo that rod's mutation and restore original anchor points
7. WHEN a rod mutation is undone THEN the Evolutionary_Infill_Generator SHALL continue to the next rod without error
8. WHEN all rods in all layers have been processed THEN the Evolutionary_Infill_Generator SHALL evaluate the mutated arrangement

### Requirement 4: Fitness-Based Selection

**User Story:** As a user, I want the generator to keep only improvements, so that the solution quality monotonically increases over time.

#### Acceptance Criteria

1. WHEN a mutation is complete THEN the Evolutionary_Infill_Generator SHALL evaluate the mutated arrangement's fitness score
2. WHEN the mutated fitness exceeds the current best fitness by at least improvement_threshold THEN the Evolutionary_Infill_Generator SHALL accept the mutation as the new baseline
3. WHEN the mutated fitness does not exceed the threshold THEN the Evolutionary_Infill_Generator SHALL discard the mutation and keep the current baseline
4. WHEN a mutation is accepted THEN the Evolutionary_Infill_Generator SHALL emit a best_result_updated signal with the improved infill
5. WHEN a mutation is accepted THEN the Evolutionary_Infill_Generator SHALL reset the stagnation counter to zero

### Requirement 5: Iteration Control

**User Story:** As a user, I want to control how long the optimization runs, so that I can balance quality against generation time.

#### Acceptance Criteria

1. THE Evolutionary_Infill_Generator SHALL accept a max_iterations parameter to limit total iterations
2. THE Evolutionary_Infill_Generator SHALL accept a max_duration_sec parameter to limit total generation time
3. WHEN max_iterations is reached THEN the Evolutionary_Infill_Generator SHALL stop and return the current best result
4. WHEN max_duration_sec is exceeded THEN the Evolutionary_Infill_Generator SHALL stop and return the current best result
5. THE Evolutionary_Infill_Generator SHALL accept a stagnation_limit parameter specifying iterations without improvement before early termination
6. WHEN stagnation_limit consecutive iterations produce no improvement THEN the Evolutionary_Infill_Generator SHALL stop and return the current best result

### Requirement 6: Progress Reporting

**User Story:** As a user, I want to see generation progress, so that I can monitor the optimization and understand how the solution is improving.

#### Acceptance Criteria

1. WHEN an iteration completes THEN the Evolutionary_Infill_Generator SHALL emit a progress_updated signal with current iteration count and elapsed time
2. WHEN a better result is found THEN the Evolutionary_Infill_Generator SHALL emit a best_result_updated signal with the improved infill
3. WHEN generation completes successfully THEN the Evolutionary_Infill_Generator SHALL emit a generation_completed signal with the final result
4. WHEN generation fails THEN the Evolutionary_Infill_Generator SHALL emit a generation_failed signal with an error message
5. WHEN generation is cancelled THEN the Evolutionary_Infill_Generator SHALL return the current best result

### Requirement 7: Rod Constraints

**User Story:** As a user, I want all generated rods to satisfy physical constraints, so that the result is manufacturable.

#### Acceptance Criteria

1. THE Evolutionary_Infill_Generator SHALL ensure all rods have both endpoints on the frame boundary
2. THE Evolutionary_Infill_Generator SHALL ensure all rods are completely within the frame boundary
3. THE Evolutionary_Infill_Generator SHALL ensure no two rods in the same layer cross each other
4. THE Evolutionary_Infill_Generator SHALL ensure all anchor points maintain minimum distance from each other
5. WHEN a mutation would violate any constraint THEN the Evolutionary_Infill_Generator SHALL reject that mutation

### Requirement 8: Parameter Configuration

**User Story:** As a user, I want to configure the evolutionary parameters, so that I can tune the optimization behavior for different use cases.

#### Acceptance Criteria

1. THE Evolutionary_Infill_Generator SHALL accept an improvement_threshold parameter (default: 0.001) for minimum fitness improvement to accept a mutation
2. THE Evolutionary_Infill_Generator SHALL read default values from Hydra configuration files
3. THE Evolutionary_Infill_Generator SHALL validate all parameters using Pydantic with appropriate constraints

### Requirement 9: Baseline Parameters

**User Story:** As a user, I want to configure the baseline generation parameters, so that I can control the initial structure of the infill.

#### Acceptance Criteria

1. THE Evolutionary_Infill_Generator SHALL accept num_rods parameter for total rods to generate
2. THE Evolutionary_Infill_Generator SHALL accept num_layers parameter for number of rod layers
3. THE Evolutionary_Infill_Generator SHALL accept main_direction_range_min_deg and main_direction_range_max_deg parameters for layer direction range
4. THE Evolutionary_Infill_Generator SHALL accept min_anchor_distance_cm parameter for minimum anchor spacing
5. THE Evolutionary_Infill_Generator SHALL accept infill_weight_per_meter_kg_m parameter for rod weight calculation
6. THE Evolutionary_Infill_Generator SHALL accept an evaluator parameter for nested evaluator configuration

### Requirement 10: UI Integration

**User Story:** As a user, I want to configure the evolutionary generator through the UI, so that I can easily adjust parameters without editing configuration files.

#### Acceptance Criteria

1. THE UI Application SHALL provide input fields for evolutionary parameters (improvement_threshold, stagnation_limit)
2. THE UI Application SHALL provide input fields for baseline parameters (num_rods, num_layers, direction range, min_anchor_distance_cm)
3. THE UI Application SHALL provide input fields for iteration control parameters (max_iterations, max_duration_sec)
4. THE UI Application SHALL load default values from configuration files
5. THE UI Application SHALL display validation errors when parameters are invalid

### Requirement 11: Logging

**User Story:** As a developer, I want comprehensive logging, so that I can debug and analyze the optimization process.

#### Acceptance Criteria

1. WHEN generation starts THEN the Evolutionary_Infill_Generator SHALL log an INFO message with all parameter values
2. WHEN the baseline is created THEN the Evolutionary_Infill_Generator SHALL log an INFO message with baseline fitness score
3. WHEN a mutation is accepted THEN the Evolutionary_Infill_Generator SHALL log an INFO message with old and new fitness scores
4. WHEN the iteration count reaches a multiple of 100 THEN the Evolutionary_Infill_Generator SHALL log an INFO message with current progress
5. WHEN generation completes THEN the Evolutionary_Infill_Generator SHALL log an INFO message with final statistics including total iterations, improvements found, and final fitness
6. WHEN stagnation causes early termination THEN the Evolutionary_Infill_Generator SHALL log an INFO message indicating stagnation

### Requirement 12: Serialization Round-Trip

**User Story:** As a developer, I want parameters to serialize and deserialize correctly, so that configurations can be saved and loaded reliably.

#### Acceptance Criteria

1. WHEN serializing EvolutionaryInfillGeneratorParameters to JSON THEN deserializing SHALL produce an equivalent object
2. WHEN serializing EvolutionaryInfillGeneratorDefaults to dict THEN deserializing SHALL produce an equivalent object
