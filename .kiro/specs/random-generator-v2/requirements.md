# Requirements Document - RandomGenerator_v2

## Introduction

This document specifies the requirements for RandomGenerator_v2, an improved random infill generator that uses a layered approach with directional control for more efficient and aesthetically pleasing rod arrangements. The generator builds upon the existing RandomGenerator (specified in `.kiro/specs/railing-infill-generator/requirements.md`) by introducing separate anchor point generation, layer-based directional constraints, and parallelizable generation logic.

**This specification extends the base railing infill generator requirements, specifically enhancing Requirement 6.1.1 (random generator parameters) with new v2 capabilities.**

## Glossary

All terms from the base railing infill generator specification apply. Additional terms specific to v2:

- **RandomGenerator_v2**: The new version of the random infill generator with layered directional approach
- **Anchor Point**: A point on the frame boundary where a rod can be attached
- **Layer**: A group of rods that share similar directional characteristics and do not cross each other
- **Main Direction**: The primary angle (relative to vertical) that rods in a layer tend to follow
- **Direction Range**: The allowable deviation from the main direction for individual rods within a layer
- **Vertical Frame Rod**: A frame boundary rod with zero or near-zero horizontal displacement (dx ≈ 0), typically the vertical posts
- **Horizontal/Sloped Frame Rod**: Any frame boundary rod that is not vertical (dx ≠ 0), such as handrails, bottom rails, or angled sections
- **Layer Iteration**: The number of attempts made to generate valid rods for a specific layer
- **Anchor Point Frame Segment**: The specific frame rod segment on which an anchor point is located

## Base Requirements

All requirements from `.kiro/specs/railing-infill-generator/requirements.md` apply to RandomGenerator_v2, including:
- Requirement 1: Random rod arrangement generation
- Requirement 1.1: Iterative improvement
- Requirement 6.1: Generator-specific parameters
- Requirement 6.1.1: Random generator parameters (extended below)
- Requirement 6.3: Maximum iteration limits
- Requirement 7: UI integration
- Requirement 9.1.1: Progress metrics

## Extended Requirements for RandomGenerator_v2

### Requirement 6.1.1-v2 (Extension)

**User Story:** As a user, I want enhanced random generator parameters with layered directional control, so that I can create more efficient and visually structured infill patterns.

**Note:** This requirement extends Requirement 6.1.1 from the base specification with additional v2-specific parameters and behaviors.

#### Acceptance Criteria - Anchor Point Distance Differentiation

**Extends base Requirement 6.1.1 criteria 6-10 (anchor point constraints)**

1. THE Generator SHALL support two separate minimum distance parameters: min_anchor_distance_vertical_cm for anchor points on vertical frame rods and min_anchor_distance_other_cm for anchor points on horizontal/sloped frame rods
2. WHEN placing an anchor point on a vertical frame rod THEN the Generator SHALL enforce the min_anchor_distance_vertical_cm constraint with other anchor points on the same vertical frame rod
3. WHEN placing an anchor point on a horizontal or sloped frame rod THEN the Generator SHALL enforce the min_anchor_distance_other_cm constraint with other anchor points on the same frame rod
4. WHEN determining which minimum distance to apply THEN the Generator SHALL identify whether the frame rod segment is vertical or horizontal/sloped based on the frame rod's geometry
5. WHEN a frame rod has zero or near-zero horizontal displacement (dx ≈ 0) THEN the Generator SHALL classify it as a vertical frame rod
6. WHEN a frame rod has non-zero horizontal displacement (dx ≠ 0) THEN the Generator SHALL classify it as a horizontal/sloped frame rod

#### Acceptance Criteria - Pre-Generation and Layer Organization

7. WHEN generation starts THEN the Generator SHALL create all anchor points before generating any rods
8. WHEN creating anchor points THEN the Generator SHALL respect the minimum distance constraint appropriate to each frame rod segment (vertical or horizontal/sloped)
9. WHEN anchor points are created THEN the Generator SHALL randomize their order
10. WHEN organizing anchor points THEN the Generator SHALL distribute them evenly across the specified number of layers
11. WHEN distributing anchor points to layers THEN the Generator SHALL ensure each layer receives an equal number of anchor points
12. WHEN the total number of anchor points is not evenly divisible by the number of layers THEN the Generator SHALL distribute remaining anchor points to layers sequentially

#### Acceptance Criteria - Layer Main Direction

13. THE Generator SHALL accept a configurable main_direction_range_min_deg parameter (default: -30°)
14. THE Generator SHALL accept a configurable main_direction_range_max_deg parameter (default: +30°)
15. WHEN distributing main directions across layers THEN the Generator SHALL divide the main direction range equally among all layers
16. WHEN there are two layers THEN the Generator SHALL assign -30° to layer 1 and +30° to layer 2 (using default range)
17. WHEN there are three layers THEN the Generator SHALL assign -30° to layer 1, 0° to layer 2, and +30° to layer 3 (using default range)
18. WHEN calculating layer main directions THEN the Generator SHALL use the formula: main_direction = min_angle + (layer_index / (num_layers - 1)) * (max_angle - min_angle) for layers with index 0 to num_layers-1
19. WHEN there is only one layer THEN the Generator SHALL use the midpoint of the main direction range as the main direction

#### Acceptance Criteria - Random Angle Deviation and Rod Generation

20. THE Generator SHALL accept a configurable random_angle_deviation_deg parameter (default: ±30°)
21. WHEN creating a rod for a layer THEN the Generator SHALL calculate a random angle offset within the range [-random_angle_deviation_deg, +random_angle_deviation_deg]
22. WHEN determining the target angle for a rod THEN the Generator SHALL add the random offset to the layer's main direction angle
23. WHEN generating a rod THEN the Generator SHALL select a random unused anchor point from the layer's anchor point pool as the start point
24. WHEN a start anchor point is selected THEN the Generator SHALL project a line from that point at the target angle (main direction + random offset)
25. WHEN projecting the line THEN the Generator SHALL calculate where the projected line intersects the frame boundary on the opposite side
26. WHEN the intersection point is found THEN the Generator SHALL search for the nearest unused anchor point from the layer's pool to the intersection point
27. WHEN the nearest anchor point is found THEN the Generator SHALL use it as the end point for the rod
28. WHEN both start and end anchor points are determined THEN the Generator SHALL create the rod geometry by connecting these two points
29. WHEN anchor points are used for a rod THEN the Generator SHALL mark both start and end anchor points as used and remove them from the available anchor point pool for that layer
30. WHEN no suitable unused anchor point is found near the intersection THEN the Generator SHALL reject the rod attempt and try again with a different start anchor point or angle

#### Acceptance Criteria - Layer-Based Generation Process

31. WHEN generating rods THEN the Generator SHALL process each layer sequentially in the initial implementation
32. WHEN processing a layer THEN the Generator SHALL iterate until a valid solution is found for that layer or the iteration limit is reached
33. WHEN tracking iterations THEN the Generator SHALL sum the iteration counts from all layers
34. WHEN checking the maximum iteration limit THEN the Generator SHALL compare against the sum of all layer iterations
35. WHEN a layer fails to generate valid rods THEN the Generator SHALL report which layer failed and how many iterations were attempted for that layer

#### Acceptance Criteria - Compatibility with Base Requirements

36. THE Generator SHALL enforce all constraints from base Requirement 6.1.1 including minimum and maximum rod length
37. THE Generator SHALL ensure rods remain within the frame boundary as specified in base Requirement 1
38. THE Generator SHALL prevent rods within the same layer from crossing each other as specified in base Requirement 1
39. THE Generator SHALL anchor all rods to the frame boundary as specified in base Requirement 6.1.1
40. THE Generator SHALL distribute rods evenly across layers as specified in base Requirement 6.1.1 criterion 12-13

#### Acceptance Criteria - UI Integration

41. THE UI Application SHALL provide input fields for min_anchor_distance_vertical_cm parameter
42. THE UI Application SHALL provide input fields for min_anchor_distance_other_cm parameter
43. THE UI Application SHALL provide input fields for main_direction_range_min_deg parameter
44. THE UI Application SHALL provide input fields for main_direction_range_max_deg parameter
45. THE UI Application SHALL provide input fields for random_angle_deviation_deg parameter
46. THE UI Application SHALL load default values for all v2 parameters from configuration files

#### Acceptance Criteria - Configuration and Validation

47. THE Generator SHALL read RandomGeneratorDefaults_v2 from Hydra configuration files
48. THE Generator SHALL use RandomGeneratorParameters_v2 with Pydantic validation
49. WHEN validating parameters THEN the Generator SHALL ensure min_anchor_distance_vertical_cm is greater than zero
50. WHEN validating parameters THEN the Generator SHALL ensure min_anchor_distance_other_cm is greater than zero
51. WHEN validating parameters THEN the Generator SHALL ensure main_direction_range_min_deg is between -90 and 90
52. WHEN validating parameters THEN the Generator SHALL ensure main_direction_range_max_deg is between -90 and 90
53. WHEN validating parameters THEN the Generator SHALL ensure main_direction_range_min_deg is less than main_direction_range_max_deg
54. WHEN validating parameters THEN the Generator SHALL ensure random_angle_deviation_deg is greater than or equal to zero

#### Acceptance Criteria - Progress and Statistics

55. WHEN generation progresses THEN the Generator SHALL emit progress_updated signals compatible with base Requirement 9.1.1
56. WHEN a better result is found THEN the Generator SHALL emit best_result_updated signals as specified in base requirements
57. WHEN generation completes successfully THEN the Generator SHALL emit generation_completed signal as specified in base requirements
58. WHEN generation fails THEN the Generator SHALL emit generation_failed signal with an error message
59. WHEN generation completes THEN the Generator SHALL provide GenerationStatistics with metrics including total iterations used (sum across all layers), duration, and rod counts

#### Acceptance Criteria - Logging

60. WHEN anchor point generation starts THEN the Generator SHALL log an INFO message indicating the start of anchor point generation
61. WHEN anchor points are generated THEN the Generator SHALL log an INFO message with the total number of anchor points created
62. WHEN anchor points are distributed to layers THEN the Generator SHALL log an INFO message with the number of anchor points assigned to each layer
63. WHEN generation for a layer starts THEN the Generator SHALL log an INFO message indicating which layer is being processed and its main direction angle
64. WHEN generation for a layer completes successfully THEN the Generator SHALL log an INFO message with the layer number, number of rods generated, and iterations used
65. WHEN generation for a layer fails THEN the Generator SHALL log a WARNING message with the layer number and reason for failure
66. WHEN the iteration count reaches a multiple of 1000 THEN the Generator SHALL log an INFO message with current progress including total iterations, current layer, and elapsed time
67. WHEN generation completes THEN the Generator SHALL log an INFO message with final statistics including total iterations across all layers, total duration, and total rods generated
