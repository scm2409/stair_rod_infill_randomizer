# Implementation Plan

## Task Overview

This implementation plan fixes the rod distribution issue in the Uniform Directional Generator. The fix modifies the `_generate_line_pattern()` method to calculate the actual polygon extent instead of using the bounding box, ensuring even distribution across the entire frame area.

## Tasks

- [x] 1. Implement polygon extent calculation
  - [x] 1.1 Add `_calculate_polygon_extent()` helper method
    - Accept polygon and perpendicular direction vector as parameters
    - Project all polygon boundary vertices onto the perpendicular direction
    - Return tuple of (min_projection, max_projection)
    - _Requirements: 1.1, 1.2, 3.1_

  - [x] 1.2 Write property test for polygon extent calculation
    - **Property 1: Polygon Extent Calculation**
    - **Validates: Requirements 1.1, 1.2**
    - Generate random convex polygons and direction angles
    - Verify calculated extent matches expected vertex projections

- [x] 2. Fix line pattern generation
  - [x] 2.1 Modify `_generate_line_pattern()` to use polygon extent
    - Replace bounding box corner projection with `_calculate_polygon_extent()` call
    - Calculate line offsets from actual min_proj to max_proj
    - Generate lines at calculated offsets instead of bounding box-relative positions
    - _Requirements: 1.3, 1.4, 1.5, 2.1, 2.2, 2.3_

  - [x] 2.2 Write property test for even distribution
    - **Property 2: Even Distribution Across Polygon Extent**
    - **Validates: Requirements 1.3, 1.4, 1.5, 2.1, 2.3**
    - Generate random frames and parameters
    - Verify lines are evenly spaced across actual polygon extent
    - Verify first/last lines are at polygon edges

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

