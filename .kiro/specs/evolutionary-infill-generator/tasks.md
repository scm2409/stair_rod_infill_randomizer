# Implementation Plan: Evolutionary Infill Generator

- [x] 1. Create parameter classes
  - [x] 1.1 Create EvolutionaryInfillGeneratorDefaults dataclass
    - Create `src/railing_generator/domain/infill_generators/evolutionary_infill_generator_parameters.py`
    - Define dataclass with baseline params (same as UniformDirectionalGenerator) plus evolutionary params
    - Include: num_rods, num_layers, direction range, min_anchor_distance_cm, infill_weight_per_meter_kg_m
    - Include: max_iterations, max_duration_sec, improvement_threshold, stagnation_limit
    - _Requirements: 8.1, 8.2, 9.1-9.6_

  - [x] 1.2 Create EvolutionaryInfillGeneratorParameters Pydantic model
    - Define Pydantic model with all parameters and validation
    - Add type discriminator: `type: Literal["evolutionary"]`
    - Add model_validator for direction range validation
    - Include nested evaluator parameter (EvaluatorParametersUnion)
    - Add from_defaults() class method
    - _Requirements: 8.3, 9.1-9.6_

  - [x] 1.3 Write property test for parameter validation
    - **Property 9: Parameter Validation**
    - **Validates: Requirements 8.3, 9.1-9.6**

  - [x] 1.4 Write property test for serialization round-trip
    - **Property 10: Serialization Round-Trip**
    - **Validates: Requirements 12.1, 12.2**

- [x] 2. Create Hydra configuration
  - [x] 2.1 Create conf/generators/evolutionary.yaml
    - Define all default values matching EvolutionaryInfillGeneratorDefaults
    - _Requirements: 8.2_

  - [x] 2.2 Register with Hydra ConfigStore
    - Add ConfigStore registration in parameters file
    - _Requirements: 8.2_

- [x] 3. Implement core generator class
  - [x] 3.1 Create EvolutionaryInfillGenerator class skeleton
    - Create `src/railing_generator/domain/infill_generators/evolutionary_infill_generator.py`
    - Inherit from Generator base class
    - Define PARAMETER_TYPE = EvolutionaryInfillGeneratorParameters
    - Implement generate() method signature
    - _Requirements: 1.1, 6.1-6.5_

  - [x] 3.2 Implement baseline generation (reuse UniformDirectionalGenerator logic)
    - Copy/adapt _generate_anchor_grid() from UniformDirectionalGenerator
    - Copy/adapt _calculate_layer_directions() from UniformDirectionalGenerator
    - Copy/adapt _generate_layer_rods() from UniformDirectionalGenerator
    - Evaluate baseline fitness and emit best_result_updated signal
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1_

  - [x] 3.3 Write property test for baseline layer distribution
    - **Property 1: Baseline Layer Distribution**
    - **Validates: Requirements 1.2, 1.3**

  - [x] 3.4 Write property test for anchor count invariance
    - **Property 2: Anchor Count Invariance**
    - **Validates: Requirements 2.1, 2.2**

- [x] 4. Implement mutation operations
  - [x] 4.1 Implement _find_next_free_anchor() helper
    - Find nearest free anchor along frame boundary in given direction (cw/ccw)
    - Handle wrap-around at boundary ends
    - Return None if no free anchor found
    - _Requirements: 3.2, 3.3_

  - [x] 4.2 Implement _mutate_rod() helper
    - Release original anchor points (mark free, clear layer)
    - Find next free anchors for both endpoints
    - Check for same-layer crossings
    - If valid: claim new anchors and update rod geometry
    - If invalid: restore original anchors and return unchanged
    - _Requirements: 2.3, 2.4, 2.5, 3.2, 3.4, 3.5, 3.6, 3.7_

  - [x] 4.3 Implement _mutate_arrangement() method
    - Deep copy current arrangement and anchor state
    - Process each layer sequentially
    - For each rod in layer: call _mutate_rod()
    - Return mutated arrangement
    - _Requirements: 3.1, 3.8_

  - [x] 4.4 Write property test for anchor state consistency
    - **Property 3: Anchor State Consistency**
    - **Validates: Requirements 2.3, 2.4, 2.5**

  - [x] 4.5 Write property test for no same-layer crossings
    - **Property 4: No Same-Layer Crossings**
    - **Validates: Requirements 3.6, 7.3**

- [x] 5. Implement evolutionary optimization loop
  - [x] 5.1 Implement main optimization loop in generate()
    - Initialize with baseline as current best
    - Loop: mutate, evaluate, select if improved
    - Track stagnation counter
    - Emit progress_updated signal each iteration
    - Emit best_result_updated when improvement found
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 5.2 Implement termination conditions
    - Check max_iterations limit
    - Check max_duration_sec limit
    - Check stagnation_limit
    - Check cancellation flag
    - Emit generation_completed or generation_failed signal
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.3, 6.4, 6.5_

  - [x] 5.3 Write property test for fitness monotonicity
    - **Property 5: Fitness Monotonicity**
    - **Validates: Requirements 4.2, 4.3**

  - [x] 5.4 Write property test for termination limits
    - **Property 8: Termination Limits**
    - **Validates: Requirements 5.3, 5.4**

- [x] 6. Implement constraint validation
  - [x] 6.1 Implement rod boundary constraint checks
    - Verify endpoints on frame boundary
    - Verify rod geometry within frame boundary
    - _Requirements: 7.1, 7.2_

  - [x] 6.2 Write property test for rod boundary constraints
    - **Property 6: Rod Boundary Constraints**
    - **Validates: Requirements 7.1, 7.2**

  - [x] 6.3 Write property test for minimum anchor distance
    - **Property 7: Minimum Anchor Distance**
    - **Validates: Requirements 7.4**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Register generator in factory
  - [x] 8.1 Update GeneratorFactory
    - Add import for EvolutionaryInfillGenerator
    - Add "evolutionary": EvolutionaryInfillGenerator to _GENERATOR_TYPES
    - _Requirements: 10.1_

- [x] 9. Create UI parameter widget
  - [x] 9.1 Create EvolutionaryInfillGeneratorParameterWidget class
    - Create widget in `src/railing_generator/presentation/generator_parameter_widget.py`
    - Inherit from GeneratorParameterWidget
    - Copy baseline fields from UniformDirectionalGeneratorParameterWidget
    - Add evolutionary parameter fields (max_iterations, max_duration_sec, improvement_threshold, stagnation_limit)
    - Include evaluator selection (same as UniformDirectionalGenerator)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 9.2 Update parameter_panel.py
    - Add import for EvolutionaryInfillGeneratorParameterWidget
    - Add case for "evolutionary" generator type
    - _Requirements: 10.1_

- [x] 10. Add logging
  - [x] 10.1 Add INFO logging throughout generator
    - Log generation start with all parameters
    - Log baseline creation with fitness score
    - Log mutation acceptance with old/new fitness
    - Log progress every 100 iterations
    - Log completion with final statistics
    - Log stagnation if early termination
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [x] 11. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
