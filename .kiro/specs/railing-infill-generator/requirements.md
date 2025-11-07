# Requirements Document

## Introduction

This document specifies the requirements for a railing infill calculator application that generates random arrangements of vertical bars (rods/balusters) to fill the space in a railing system. The application will calculate and visualize the placement of randomly positioned bars within defined railing dimensions.

## Glossary

- **Railing System**: The complete railing structure consisting of top rail, bottom rail, and infill area
- **Infill Area**: The space between the top and bottom rails that needs to be filled with vertical bars
- **Vertical Bar**: A rod or baluster that fills the space between rails (also called baluster or spindle)
- **Random Arrangement**: A non-uniform distribution of bars with varying spacing and angles
- **Bar Angle**: The angle of inclination of a vertical bar from true vertical (0° = perfectly vertical)
- **Bar Layer**: A depth layer in which bars are placed; bars in the same layer cannot overlap, but bars in different layers can cross
- **Layer Configuration**: The number of depth layers used for bar placement
- **Bar Generator**: The component that calculates random positions for vertical bars
- **Visualization Component**: The UI component that displays the generated railing design
- **Stair Profile**: The stepped bottom rail that follows the stair treads
- **Step Configuration**: The dimensions and positions of individual stair steps

## Requirements

### Requirement 1

**User Story:** As a user, I want to define the dimensions of my railing, so that the application can calculate the appropriate infill

#### Acceptance Criteria

1. THE Railing System SHALL accept input for total railing length
2. THE Railing System SHALL accept input for railing height at the highest point
3. THE Railing System SHALL accept input for bar diameter
4. THE Railing System SHALL accept input for stair step dimensions (tread depth and riser height)
5. THE Railing System SHALL accept input for the number of steps
6. THE Railing System SHALL accept input for the number of bar layers
7. THE Railing System SHALL validate that all dimension inputs are positive numbers
8. THE Railing System SHALL validate that the number of layers is at least 1
9. THE Railing System SHALL store dimension values for use in calculations

### Requirement 2

**User Story:** As a user, I want to generate a random arrangement of vertical bars in multiple layers, so that I get a unique and aesthetically pleasing railing design with depth

#### Acceptance Criteria

1. THE Bar Generator SHALL create random positions for vertical bars within the infill area
2. THE Bar Generator SHALL distribute bars across all defined layers
3. THE Bar Generator SHALL assign a random angle to each bar within the defined angle range
4. THE Bar Generator SHALL ensure bars within the same layer do not overlap with each other
5. THE Bar Generator SHALL allow bars from different layers to cross or overlap each other
6. THE Bar Generator SHALL distribute bars across the entire railing length
7. THE Bar Generator SHALL calculate individual bar heights based on the stair step profile
8. WHEN a bar is positioned over a step, THE Bar Generator SHALL set the bar height to reach from that step to the top rail
9. THE Bar Generator SHALL generate a new random arrangement each time the generation is triggered
10. THE Bar Generator SHALL respect minimum and maximum spacing constraints between bars within the same layer

### Requirement 3

**User Story:** As a user, I want to specify constraints for bar spacing and angles, so that the railing meets safety and aesthetic requirements

#### Acceptance Criteria

1. THE Railing System SHALL accept input for minimum spacing between bars
2. THE Railing System SHALL accept input for maximum spacing between bars
3. THE Railing System SHALL accept input for maximum angle deviation from vertical (in degrees)
4. THE Bar Generator SHALL enforce minimum spacing to prevent bars from being too close
5. THE Bar Generator SHALL enforce maximum spacing to prevent gaps that are too large
6. THE Bar Generator SHALL randomize bar angles within the range of -max_angle to +max_angle degrees
7. THE Railing System SHALL validate that minimum spacing is less than maximum spacing
8. THE Railing System SHALL validate that maximum angle is between 0 and 45 degrees

### Requirement 4

**User Story:** As a user, I want to visualize the generated railing design, so that I can see how the random arrangement looks with depth layers

#### Acceptance Criteria

1. THE Visualization Component SHALL display the railing with a straight top rail
2. THE Visualization Component SHALL display the stepped bottom rail following the stair profile
3. THE Visualization Component SHALL display all generated vertical bars in their calculated positions
4. THE Visualization Component SHALL render bars with correct diameter, spacing, individual heights, and angles
5. THE Visualization Component SHALL display bars as angled lines when angle deviation is applied
6. THE Visualization Component SHALL visually distinguish bars from different layers (e.g., using color, opacity, or depth cues)
7. THE Visualization Component SHALL render bars from different layers so that crossing bars are visible
8. THE Visualization Component SHALL display the stair steps beneath the railing
9. THE Visualization Component SHALL update the display when a new arrangement is generated
10. THE Visualization Component SHALL provide a clear visual representation of the railing dimensions and stair profile

### Requirement 5

**User Story:** As a user, I want to regenerate the bar arrangement, so that I can explore different random configurations

#### Acceptance Criteria

1. THE Railing System SHALL provide a regenerate function to create new arrangements
2. WHEN the user triggers regeneration, THE Bar Generator SHALL create a completely new random arrangement
3. THE Visualization Component SHALL update to show the new arrangement immediately
4. THE Railing System SHALL maintain the same dimensions and constraints during regeneration
5. THE Railing System SHALL allow unlimited regenerations

### Requirement 6

**User Story:** As a user, I want to see how many bars are used in the design, so that I can plan material requirements

#### Acceptance Criteria

1. THE Bar Generator SHALL count the total number of bars in the generated arrangement
2. THE Railing System SHALL display the bar count to the user
3. THE Railing System SHALL update the bar count when a new arrangement is generated
4. THE Railing System SHALL calculate total material length needed (bar count × height)
5. THE Railing System SHALL display material requirements in a clear format

### Requirement 7

**User Story:** As a user, I want to save and load railing configurations, so that I can work on multiple designs

#### Acceptance Criteria

1. THE Railing System SHALL save railing dimensions and constraints to a file
2. THE Railing System SHALL save the current bar arrangement to a file
3. THE Railing System SHALL load previously saved configurations from a file
4. THE Railing System SHALL restore both dimensions and bar positions when loading
5. THE Railing System SHALL use a standard file format for configuration storage

### Requirement 8

**User Story:** As a user, I want to export the railing design, so that I can use it for fabrication or documentation

#### Acceptance Criteria

1. THE Railing System SHALL export the design as an image file
2. THE Railing System SHALL export bar positions as a data file (CSV or JSON)
3. THE Railing System SHALL include dimensions and bar count in the export
4. THE Railing System SHALL support multiple export formats
5. THE Railing System SHALL allow the user to specify export file location
