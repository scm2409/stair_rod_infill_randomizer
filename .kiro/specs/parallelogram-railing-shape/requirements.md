# Requirements Document

## Introduction

This specification defines a new railing shape type called "Parallelogram Railing Shape" for the railing infill generator application. Unlike the staircase shape which has a stepped bottom boundary following stair treads and risers, the parallelogram shape features a straight bottom edge that runs parallel to the angled handrail. This creates a parallelogram-shaped frame that is useful for continuous slope railings (ramps, inclined walkways) where no individual steps exist.

## Glossary

- **Parallelogram_Railing_Shape**: A railing frame shape where the top (handrail) and bottom edges are parallel angled lines, connected by two vertical posts
- **Handrail**: The top angled edge of the railing frame that users grip for support
- **Post**: A vertical rod at either end of the railing frame
- **Bottom_Rail**: The lower angled edge of the frame, parallel to the handrail
- **Post_Length_cm**: The vertical height of each post in centimeters
- **Slope_Width_cm**: The horizontal distance between the left and right posts
- **Slope_Height_cm**: The vertical rise from the base of the left post to the base of the right post
- **Frame_Weight_Per_Meter_kg_m**: The weight of the frame material per meter length

## Requirements

### Requirement 1

**User Story:** As a railing designer, I want to create parallelogram-shaped railing frames, so that I can design infills for continuous slope railings like ramps.

#### Acceptance Criteria

1. WHEN a user selects the parallelogram shape type THEN the Parallelogram_Railing_Shape SHALL generate a frame with four rods: left post, handrail, right post, and bottom rail
2. WHEN the Parallelogram_Railing_Shape generates a frame THEN the handrail and bottom rail SHALL be parallel to each other
3. WHEN the Parallelogram_Railing_Shape generates a frame THEN both posts SHALL be vertical (perpendicular to the horizontal axis)
4. WHEN the Parallelogram_Railing_Shape generates a frame THEN the left post SHALL start at origin (0, 0) and extend upward by Post_Length_cm
5. WHEN the Parallelogram_Railing_Shape generates a frame THEN the right post base SHALL be positioned at (Slope_Width_cm, Slope_Height_cm)

### Requirement 2

**User Story:** As a railing designer, I want to configure the parallelogram shape dimensions, so that I can match the physical railing specifications.

#### Acceptance Criteria

1. WHEN configuring the Parallelogram_Railing_Shape THEN the system SHALL accept Post_Length_cm as a positive value
2. WHEN configuring the Parallelogram_Railing_Shape THEN the system SHALL accept Slope_Width_cm as a positive value
3. WHEN configuring the Parallelogram_Railing_Shape THEN the system SHALL accept Slope_Height_cm as a positive value
4. WHEN configuring the Parallelogram_Railing_Shape THEN the system SHALL accept Frame_Weight_Per_Meter_kg_m as a positive value
5. WHEN a user provides invalid parameter values (zero or negative) THEN the system SHALL reject the configuration with a validation error

### Requirement 3

**User Story:** As a user, I want default configuration values for the parallelogram shape, so that I can quickly create a standard railing without specifying every parameter.

#### Acceptance Criteria

1. WHEN loading the parallelogram shape THEN the system SHALL provide sensible default values for all parameters
2. WHEN creating a new parallelogram shape THEN the system SHALL use the default values if the user does not specify custom values

### Requirement 4

**User Story:** As a user, I want to save and load railing projects that use the parallelogram shape, so that I can continue my work later.

#### Acceptance Criteria

1. WHEN saving a project with a parallelogram shape THEN the system SHALL persist all shape parameters
2. WHEN loading a project with a parallelogram shape THEN the system SHALL restore all shape parameters exactly as saved
