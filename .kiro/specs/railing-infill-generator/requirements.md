# Requirements Document

## Introduction

This document specifies the requirements for a railing infill generator application that calculates and generates random rod arrangements for filling railing frames. The application supports multiple railing shapes with extensible parameters and generates visual representations of the rod placements.

## Glossary

- **Railing Frame**: The outer boundary structure that defines the shape and dimensions of the railing
- **Infill**: The interior filling of the railing frame consisting of randomly arranged rods
- **Rod**: A vertical or angled bar element used to fill the railing frame
- **Shape Type**: The geometric configuration of the railing frame (e.g., stair, rectangular)
- **Generator**: The system component that calculates and creates the rod arrangement
- **Generator Type**: The specific algorithm or strategy used for generating infill (e.g., random placement, neuronal-network-based)
- **UI Application**: The graphical user interface for interacting with the generator
- **Shape Parameters**: The dimensional values that define a specific railing frame shape
- **Infill Parameters**: The configuration values that control rod placement and arrangement for a specific shape
- **Generator Parameters**: The configuration values specific to a generator type that control its behavior
- **Quality Evaluator**: The component that assesses the quality of a generated infill arrangement (fitness function)
- **Evaluation Criteria**: The rules and metrics used to determine if an infill arrangement is acceptable
- **Iteration**: A single attempt at generating an infill arrangement within an iterative generation process

## Requirements

### Requirement 1

**User Story:** As a user, I want to generate random rod arrangements for railing infill, so that I can create unique filling patterns for railing frames

#### Acceptance Criteria

1. THE Generator SHALL create random arrangements of rods within the railing frame boundaries
2. THE Generator SHALL ensure rods do not overlap with each other
3. THE Generator SHALL ensure rods remain within the railing frame boundaries
4. THE Generator SHALL produce different arrangements on each generation request
5. THE Generator SHALL calculate the positions and dimensions for all rods in the infill

### Requirement 1.1

**User Story:** As a user, I want the random generator to iteratively improve results, so that I receive high-quality infill arrangements

#### Acceptance Criteria

1. THE Generator SHALL evaluate each generated arrangement using quality criteria (fitness function)
2. THE Generator SHALL iterate and generate new arrangements until an acceptable solution is found
3. THE Generator SHALL respect a maximum iteration limit to prevent infinite loops
4. WHEN the maximum iteration limit is reached, THE Generator SHALL return the best arrangement found
5. THE Generator SHALL log the number of iterations performed during generation

### Requirement 2

**User Story:** As a user, I want to define stair-shaped railing frames, so that I can generate infill for staircase railings

#### Acceptance Criteria

1. THE Railing Frame SHALL support stair shape type as a configuration option
2. THE Railing Frame SHALL accept post length parameter for the vertical posts
3. THE Railing Frame SHALL accept stair height parameter for the vertical distance between first and second post
4. THE Railing Frame SHALL accept number of steps parameter
5. THE Railing Frame SHALL define the frame with two vertical posts of equal length on left and right sides
6. THE Railing Frame SHALL connect the top of the posts with a straight line representing the handrail
7. THE Railing Frame SHALL define the bottom boundary following the stair steps rather than a straight line
8. THE Railing Frame SHALL validate stair parameters for geometric consistency
9. THE Generator SHALL generate rod arrangements that fit within the stair-shaped boundary

### Requirement 3

**User Story:** As a user, I want to define rectangular railing frames, so that I can generate infill for flat railings

#### Acceptance Criteria

1. THE Railing Frame SHALL support rectangular shape type as a configuration option
2. THE Railing Frame SHALL accept width and height parameters for rectangular shapes
3. THE Railing Frame SHALL validate rectangular parameters for positive dimensions
4. THE Generator SHALL generate rod arrangements that fit within the rectangular boundary

### Requirement 4

**User Story:** As a developer, I want an extensible shape system, so that new railing shapes can be added in the future without major refactoring

#### Acceptance Criteria

1. THE Railing Frame SHALL use a plugin-based or inheritance-based architecture for shape types
2. THE Railing Frame SHALL define a common interface for all shape types
3. WHEN a new shape type is added, THE Railing Frame SHALL support it without modifying existing shape implementations
4. THE Railing Frame SHALL allow each shape type to define its own specific parameters
5. THE Railing Frame SHALL allow each shape type to define default parameter values in configuration files

### Requirement 4.1

**User Story:** As a developer, I want an extensible generator system, so that new infill generation algorithms can be added in the future

#### Acceptance Criteria

1. THE Generator SHALL use a plugin-based or inheritance-based architecture for generator types
2. THE Generator SHALL define a common interface for all generator types
3. WHEN a new generator type is added, THE Generator SHALL support it without modifying existing generator implementations
4. THE Generator SHALL allow each generator type to define its own specific parameters
5. THE Generator SHALL allow each generator type to define default parameter values in configuration files

### Requirement 5

**User Story:** As a user, I want to configure shape-specific parameters, so that I can precisely define the dimensions of my railing frame

#### Acceptance Criteria

1. THE UI Application SHALL provide input fields for shape-specific dimensional parameters
2. WHEN a shape type is selected, THE UI Application SHALL display only the relevant parameters for that shape
3. THE Railing Frame SHALL validate all dimensional parameters before generation
4. THE UI Application SHALL provide clear error messages for invalid parameter values
5. THE UI Application SHALL provide input for frame rod weight per meter parameter
6. THE UI Application SHALL use centimeters as the default unit for all length measurements
7. THE UI Application SHALL load default frame rod weight per meter from configuration files

### Requirement 6

**User Story:** As a user, I want to configure infill parameters, so that I can control how the rods are arranged within the frame

#### Acceptance Criteria

1. THE UI Application SHALL provide input fields for infill-specific parameters
2. THE Generator SHALL accept infill parameters that control rod placement behavior
3. THE Generator SHALL apply infill parameters consistently across all shape types
4. THE Railing Frame SHALL allow each shape type to define shape-specific infill constraints
5. THE UI Application SHALL provide input for infill rod weight per meter parameter
6. THE UI Application SHALL load default infill parameter values from configuration files
7. THE UI Application SHALL load default infill rod weight per meter from configuration files
8. THE UI Application SHALL allow users to modify infill parameters in the GUI

### Requirement 6.1

**User Story:** As a user, I want to configure generator-specific parameters, so that I can control the behavior of different generation algorithms

#### Acceptance Criteria

1. THE UI Application SHALL provide input fields for generator-specific parameters
2. WHEN a generator type is selected, THE UI Application SHALL display only the relevant parameters for that generator
3. THE Generator SHALL accept generator-specific parameters that control its algorithm behavior
4. THE UI Application SHALL load default generator parameter values from configuration files
5. THE UI Application SHALL allow users to modify generator parameters in the GUI

### Requirement 6.2

**User Story:** As a user, I want to configure quality evaluation criteria for the random generator, so that I can control what constitutes an acceptable infill arrangement

#### Acceptance Criteria

1. THE Quality Evaluator SHALL accept configurable evaluation criteria parameters
2. THE Quality Evaluator SHALL assess generated arrangements against the defined criteria
3. THE Quality Evaluator SHALL return a quality score or pass/fail result for each arrangement
4. THE UI Application SHALL provide input fields for evaluation criteria parameters
5. THE UI Application SHALL load default evaluation criteria from configuration files

### Requirement 6.3

**User Story:** As a user, I want to configure the maximum iteration limit for the random generator, so that I can balance quality with generation time

#### Acceptance Criteria

1. THE Generator SHALL accept a maximum iteration limit parameter
2. THE Generator SHALL accept a maximum duration limit parameter
3. THE Generator SHALL stop iterating when one of the maximum limit is reached
4. THE Generator SHALL stop iterating when an acceptable arrangement is found before a maximum limit is reached
5. THE UI Application SHALL provide an input field for maximum iteration limit and duration limit
6. THE UI Application SHALL load a default maximum iteration/duration value from configuration files
7. THE UI Application SHALL stop if cancel is clicked during generation and should show the best result generated so far.

### Requirement 7

**User Story:** As a user, I want a graphical interface to interact with the generator, so that I can easily create and visualize railing infill designs

#### Acceptance Criteria

1. THE UI Application SHALL provide a graphical user interface
2. THE UI Application SHALL display a vector-based viewport with visual representation of the railing frame and infill
3. THE UI Application SHALL render frame and infill as simple lines in the viewport
4. THE UI Application SHALL allow users to select shape types from available options
5. THE UI Application SHALL allow users to select generator types from available options
6. THE UI Application SHALL provide an "Update Shape" button to render the frame without infill (short-running poeration)
7. THE UI Application SHALL provide a "Generate Infill" button to trigger infill generation (long-running operation)
8. THE UI Application SHALL update the viewport visualization when shape or infill is updated
9. THE UI Application SHALL dynamically update parameter input fields based on selected shape and generator types

### Requirement 7.1

**User Story:** As a user, I want to preview the railing frame shape before generating infill, so that I can verify the dimensions are correct

#### Acceptance Criteria

1. WHEN the "Update Shape" button is pressed, THE UI Application SHALL render the railing frame in the viewport without infill
2. THE UI Application SHALL complete shape rendering quickly as a short-running operation
3. THE UI Application SHALL display the frame boundary based on current shape parameters
4. THE UI Application SHALL clear any existing infill from the viewport when updating shape

### Requirement 7.2

**User Story:** As a user, I want to zoom and pan the viewport, so that I can examine details and navigate large designs

#### Acceptance Criteria

1. WHEN the user scrolls the mouse wheel, THE UI Application SHALL zoom the viewport in or out
2. THE UI Application SHALL use the mouse cursor position as the zoom origin
3. THE UI Application SHALL support panning the viewport using mouse drag operations
4. THE UI Application SHALL maintain smooth viewport navigation during zoom and pan operations

### Requirement 7.3

**User Story:** As a user, I want to enumerate and identify individual lines, so that I can reference specific frame or infill elements

#### Acceptance Criteria

1. THE UI Application SHALL provide a toggle control to show or hide line enumeration
2. WHEN enumeration is visible, THE UI Application SHALL display a numbered marker for each infill line
3. WHEN enumeration is visible, THE UI Application SHALL display a numbered marker for each frame line
4. THE UI Application SHALL use circles with counter numbers for infill line markers
5. THE UI Application SHALL use squares with counter numbers for frame line markers
6. THE UI Application SHALL connect each marker to its target line with a dashed anchor line
7. THE UI Application SHALL position markers outside the frame boundary to minimize view obstruction
8. THE UI Application SHALL arrange markers to minimize anchor line crossings with each other

### Requirement 8

**User Story:** As a user, I want to view a bill of materials for the railing, so that I can understand the parts needed for manufacturing

#### Acceptance Criteria

1. THE UI Application SHALL display a bill of materials (BOM) table viewport
2. THE UI Application SHALL organize the BOM table with two tabs: one for frame parts and one for infill parts
3. THE UI Application SHALL display the following columns in each BOM table: unique ID number, length, cut angle at start, cut angle at end, and weight
4. THE UI Application SHALL calculate part weight using length and weight per meter parameters
5. THE UI Application SHALL calculate and display accurate values for all BOM columns based on the generated design
6. THE UI Application SHALL display total length sum for each table tab
7. THE UI Application SHALL display total weight sum for each table tab
8. THE UI Application SHALL display combined total length sum for both frame and infill parts
9. THE UI Application SHALL display combined total weight sum for both frame and infill parts
10. THE UI Application SHALL update the BOM table and totals when a new design is generated

### Requirement 8.1

**User Story:** As a user, I want to select parts in the BOM table and see them highlighted in the viewport, so that I can identify specific parts visually

#### Acceptance Criteria

1. WHEN a user selects an entry in the BOM table, THE UI Application SHALL highlight the corresponding part in the main viewport
2. THE UI Application SHALL maintain the highlight until a different part is selected or the selection is cleared
3. THE UI Application SHALL provide visual distinction for highlighted parts compared to non-highlighted parts
4. THE UI Application SHALL support selection in both frame parts and infill parts tabs

### Requirement 8.2

**User Story:** As a user, I want to save and load railing designs, so that I can preserve my work and share designs with others

#### Acceptance Criteria

1. THE UI Application SHALL provide a main menu with save and load actions
2. WHEN saving, THE UI Application SHALL export all parameters as a JSON file
3. WHEN saving, THE UI Application SHALL export the viewport visualization as a PNG image
4. THE UI Application SHALL render the PNG with the viewport zoomed to show the entire design
5. THE UI Application SHALL use a configurable resolution for PNG export from configuration files
6. WHEN saving, THE UI Application SHALL export the frame parts BOM table as a CSV file
7. WHEN saving with generated infill, THE UI Application SHALL export the infill parts BOM table as a CSV file
8. WHEN loading, THE UI Application SHALL restore all parameters from the JSON file
9. THE UI Application SHALL allow users to specify save and load file locations

### Requirement 9

**User Story:** As a user, I want to regenerate infill with the same parameters, so that I can explore different random arrangements

#### Acceptance Criteria

1. THE UI Application SHALL provide a regenerate button or command
2. WHEN regenerate is triggered, THE Generator SHALL create a new random arrangement using the current parameters
3. THE Generator SHALL produce a different arrangement on each regeneration
4. THE UI Application SHALL update the visualization with the new arrangement

### Requirement 9.1

**User Story:** As a user, I want visual feedback during long-running operations, so that I know the application is working and can monitor progress

#### Acceptance Criteria

1. WHEN a long-running operation is in progress, THE UI Application SHALL display a progress dialog
2. THE UI Application SHALL show progress information in the progress dialog
3. THE UI Application SHALL display progress logs in the progress dialog
4. THE UI Application SHALL block input to the main application window while the progress dialog is visible
5. THE UI Application SHALL close the progress dialog when the operation completes
6. THE UI Application SHALL display a cancel button to clancel the current operation.

### Requirement 9.2

**User Story:** As a user, I want the interface to indicate when short operations are running, so that I don't accidentally trigger multiple operations

#### Acceptance Criteria

1. WHEN a short-running operation is in progress, THE UI Application SHALL disable all input elements
2. THE UI Application SHALL visually indicate disabled state by graying out input elements
3. THE UI Application SHALL not display a progress dialog for short-running operations
4. THE UI Application SHALL re-enable input elements when the short operation completes

### Requirement 10

**User Story:** As a user, I want default parameter values stored in configuration files, so that I have sensible starting values for all parameters

#### Acceptance Criteria

1. THE UI Application SHALL store default shape parameter values in configuration files
2. THE UI Application SHALL store default infill parameter values in configuration files
3. THE UI Application SHALL store default generator parameter values in configuration files
4. THE UI Application SHALL organize configuration files by shape type and generator type
5. THE UI Application SHALL load default values from configuration on startup
