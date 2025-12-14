# Requirements Document

## Introduction

This document specifies the requirements for fixing the rod distribution issue in the Uniform Directional Generator. The current implementation creates gaps at the edges of the frame because it calculates line positions based on the bounding box center rather than the actual polygon extent in the perpendicular direction. This fix ensures that infill rods are evenly distributed across the entire frame area by finding the actual first and last valid rod positions within the frame for each layer direction.

## Glossary

All terms from the base uniform directional generator specification (`.kiro/specs/uniform-directional-generator/requirements.md`) apply. Additional terms specific to this fix:

- **Perpendicular_Direction**: The direction perpendicular to a layer's main direction, used for spacing parallel lines
- **Polygon_Extent**: The actual range of the polygon when projected onto a given direction
- **Vertex_Projection**: The projection of a polygon vertex onto a line in a given direction
- **First_Valid_Line**: The first parallel line (in the perpendicular direction) that intersects the frame boundary at two points
- **Last_Valid_Line**: The last parallel line (in the perpendicular direction) that intersects the frame boundary at two points
- **Effective_Range**: The distance between the first and last valid lines, representing the actual area to fill with rods

## Base Requirements

All requirements from `.kiro/specs/uniform-directional-generator/requirements.md` continue to apply. This fix modifies the implementation of Requirement 1 (even distribution) and Requirement 5 (direct calculation) without changing their intent.

## Requirements

### Requirement 1

**User Story:** As a railing designer, I want the infill rods to be evenly distributed across the entire frame area, so that there are no large gaps at the edges of the frame.

#### Acceptance Criteria

1. WHEN generating a line pattern for a layer THEN the Uniform_Directional_Generator SHALL calculate the actual polygon extent by projecting all frame boundary vertices onto the perpendicular direction
2. WHEN calculating the polygon extent THEN the Uniform_Directional_Generator SHALL find the minimum and maximum projection values to determine the effective range
3. WHEN spacing parallel lines THEN the Uniform_Directional_Generator SHALL distribute lines evenly across the effective range from minimum to maximum projection
4. THE Uniform_Directional_Generator SHALL ensure the first line passes through or near the minimum extent of the polygon
5. THE Uniform_Directional_Generator SHALL ensure the last line passes through or near the maximum extent of the polygon

### Requirement 2

**User Story:** As a railing designer, I want the rod distribution to work correctly for all frame shapes including parallelograms, so that the generator produces consistent results regardless of frame geometry.

#### Acceptance Criteria

1. WHEN the frame is a parallelogram THEN the Uniform_Directional_Generator SHALL correctly calculate the polygon extent for any layer direction
2. WHEN the frame is rectangular THEN the Uniform_Directional_Generator SHALL produce the same results as before (no regression)
3. WHEN the frame has an irregular shape THEN the Uniform_Directional_Generator SHALL still distribute rods evenly across the actual polygon extent

### Requirement 3

**User Story:** As a railing designer, I want the algorithm to be efficient, so that generation remains fast.

#### Acceptance Criteria

1. THE Uniform_Directional_Generator SHALL calculate the polygon extent in O(n) time where n is the number of boundary vertices
2. THE Uniform_Directional_Generator SHALL NOT require additional iterations or trial-and-error to find the effective range
3. THE Uniform_Directional_Generator SHALL maintain the deterministic behavior of the original implementation

