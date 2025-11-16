# Implementation Plan

This document outlines the implementation tasks for the Railing Infill Generator application. Each task builds incrementally on previous tasks, with all code integrated as it's developed.

## Task List

- [x] 1. Set up project structure and core infrastructure
  - Create project directory structure following layered architecture (domain, application, presentation, infrastructure)
  - Set up `pyproject.toml` with all dependencies (PySide6, pydantic, shapely>=2.0, hydra-core, etc.)
  - Create basic entry point (`__main__.py`) and application setup (`app.py`)
  - Set up Hydra configuration structure in `conf/` directory
  - Configure logging with RichHandler and hierarchical loggers
  - Write test for logging configuration (verify log file creation, console output, log levels)
  - **Coverage: Starting 0% → Ending 51%** ✅
  - _Requirements: 10, 11_

- [ ] 2. Implement core domain models with tests
  - [ ] 2.1 Implement Rod class (Pydantic BaseModel)
    - Define fields: geometry (LineString), start_cut_angle_deg, end_cut_angle_deg, weight_kg_m, layer
    - Implement computed fields: length_cm, weight_kg, start_point, end_point
    - Implement `to_bom_entry()` method
    - Implement `model_dump_geometry()` for serialization with geometry
    - Add validation constraints using Field()
    - Write unit tests for Rod class (validation, computed fields, serialization, BOM generation)
    - _Requirements: 1, 5, 6, 8_
  - [ ] 2.2 Implement InfillResult class (Pydantic BaseModel)
    - Define fields: rods (list), fitness_score (optional), iteration_count (optional), duration_sec (optional)
    - Implement serialization methods
    - Write unit tests for InfillResult (serialization, deserialization)
    - _Requirements: 1, 6.2, 9_

- [ ] 3. Implement Shape system with extensibility and tests
  - [ ] 3.1 Create Shape base class and interface
    - Define abstract Shape class with `get_boundary()` and `get_frame_rods()` methods
    - Write test to verify abstract methods cannot be instantiated directly
    - _Requirements: 4_
  - [ ] 3.2 Implement StairShape with tests
    - Create StairShapeDefaults dataclass for Hydra config
    - Create StairShapeParameters Pydantic model with validation
    - Implement `get_boundary()` returning Shapely Polygon
    - Implement `get_frame_rods()` returning frame Rod objects (layer=0)
    - Calculate stepped bottom boundary geometry
    - Write unit tests for StairShape (boundary calculation, frame rods, parameter validation, geometry correctness)
    - _Requirements: 2, 4, 5_
  - [ ] 3.3 Implement RectangularShape with tests
    - Create RectangularShapeDefaults dataclass for Hydra config
    - Create RectangularShapeParameters Pydantic model with validation
    - Implement `get_boundary()` returning Shapely Polygon
    - Implement `get_frame_rods()` returning frame Rod objects (layer=0)
    - Write unit tests for RectangularShape (boundary calculation, frame rods, parameter validation)
    - _Requirements: 3, 4, 5_
  - [ ] 3.4 Create Shape factory with tests
    - Implement factory function to create shapes from type string and parameters
    - Write unit tests for factory (correct type creation, error handling)
    - _Requirements: 4_
  - [ ] 3.5 Create Hydra configuration files for shapes
    - Create `conf/shapes/stair.yaml` with default values
    - Create `conf/shapes/rectangular.yaml` with default values
    - Write test to verify config files can be loaded and parsed correctly
    - _Requirements: 10_

- [ ] 4. Implement Quality Evaluator for Random Generator with tests
  - [ ] 4.1 Implement hole identification using Shapely with tests
    - Implement function to find holes using `shapely.node()` and `polygonize()`
    - Handle noded network creation for crossing rods
    - Calculate hole areas using Shapely Polygon.area
    - Write unit tests for hole identification (simple cases, crossing rods, edge cases)
    - _Requirements: 6.2, 6.2.1_
  - [ ] 4.2 Implement quality criteria calculations with tests
    - Implement hole uniformity calculation
    - Implement incircle uniformity calculation
    - Implement angle distribution scoring
    - Implement anchor spacing scoring (separate horizontal/vertical)
    - Write unit tests for each criterion (known inputs, expected scores)
    - _Requirements: 6.2.1_
  - [ ] 4.3 Implement QualityEvaluator class with tests
    - Create EvaluatorCriteriaDefaults dataclass for Hydra config
    - Implement `evaluate()` method returning fitness score
    - Implement `is_acceptable()` method checking max hole area
    - Combine criteria using configurable weights
    - Write unit tests for QualityEvaluator (fitness calculation, acceptance logic, weight combination)
    - _Requirements: 6.2, 6.2.1_
  - [ ] 4.4 Create Hydra configuration for evaluator
    - Create `conf/evaluator/criteria.yaml` with weights and thresholds
    - Write test to verify config file can be loaded and weights sum correctly
    - _Requirements: 6.2, 10_

- [ ] 5. Implement Generator system with extensibility and tests
  - [ ] 5.1 Create Generator base class (QObject)
    - Define abstract Generator class inheriting from QObject
    - Define signals: progress_updated, best_result_updated, generation_completed, generation_failed
    - Implement cancellation support with `_cancelled` flag
    - Write test to verify signals are defined correctly and cancellation flag works
    - _Requirements: 4.1, 9.1_
  - [ ] 5.2 Implement RandomGenerator with tests
    - Create RandomGeneratorDefaults dataclass for Hydra config
    - Create RandomGeneratorParameters Pydantic model with validation
    - Implement `generate()` method with iterative random placement
    - Select random anchor points along frame using LineString.interpolate()
    - Generate rods with random angles within deviation limit
    - Ensure no crossings within same layer using LineString.intersects()
    - Organize rods into configurable layers
    - Respect minimum anchor distance constraint
    - Emit progress_updated signals during generation
    - Emit best_result_updated signals when better arrangement found
    - Check cancellation flag and iteration/duration limits
    - Return best InfillResult found
    - Write unit tests for RandomGenerator (constraint enforcement, layer organization, signal emission)
    - Write integration tests for Generator + Evaluator (fitness improvement, termination conditions)
    - _Requirements: 1, 1.1, 4.1, 6.1, 6.1.1, 6.3, 9, 9.1, 9.1.1_
  - [ ] 5.3 Create Generator factory with tests
    - Implement factory function to create generators from type string
    - Write unit tests for factory
    - _Requirements: 4.1_
  - [ ] 5.4 Create Hydra configuration for generators
    - Create `conf/generators/random.yaml` with default parameters
    - Write test to verify config file can be loaded and parameters are valid
    - _Requirements: 6.1.1, 10_

- [ ] 6. Implement Application Controller and State Management with tests
  - [ ] 6.1 Implement Project State with tests
    - Create ProjectState class to hold current project data
    - Track shape type, parameters, and instance
    - Track generator type, parameters, and infill result
    - Track file path and modified flag
    - Write unit tests for ProjectState (state transitions, modified flag logic)
    - _Requirements: 8.2, 8.2.2_
  - [ ] 6.2 Implement Application Controller with tests
    - Create ApplicationController class
    - Implement `create_new_project()` method
    - Implement `update_shape(type, params)` method
    - Implement `generate_infill(type, params)` method with QThread worker
    - Implement `cancel_generation()` method
    - Implement `save_project(path)` method creating .rig.zip archive
    - Implement `load_project(path)` method extracting from .rig.zip
    - Implement `export_dxf(path)` method using ezdxf
    - Handle state transitions and modified flag updates
    - Write integration tests for ApplicationController workflows (create, update, generate, save, load)
    - Write tests for save/load round-trip (data integrity)
    - _Requirements: 7, 8.2, 8.2.1, 8.2.2, 9_
  - [ ] 6.3 Implement worker thread pattern for generation
    - Create GenerationWorker class (QObject)
    - Implement moveToThread pattern for background generation
    - Connect signals between worker, generator, and UI
    - Handle thread lifecycle (start, quit, wait)
    - Write test to verify worker can be moved to thread and signals work correctly
    - _Requirements: 9.1_

- [ ] 7. Implement Presentation Layer - Main Window
  - [ ] 7.1 Create Main Window structure
    - Create MainWindow class (QMainWindow)
    - Set up menu bar (File, View, Help)
    - Create central widget with splitter layout
    - Create status bar with operation status and stats
    - Implement window title with filename and modified indicator
    - Write test to verify window can be created and has correct structure
    - _Requirements: 7, 8.2.2_
  - [ ] 7.2 Implement File menu actions
    - Implement New Project action
    - Implement Open action with file dialog
    - Implement Save action
    - Implement Save As action with file dialog
    - Implement Export to DXF action
    - Implement Quit action with unsaved changes warning
    - Write test to verify menu actions are created and connected
    - _Requirements: 8.2, 8.2.1, 8.2.2_
  - [ ] 7.3 Implement View menu actions
    - Implement Toggle Enumeration action
    - Implement Fit to View action
    - Write test to verify view actions work correctly
    - _Requirements: 7.3_

- [ ] 8. Implement Presentation Layer - Parameter Panel
  - [ ] 8.1 Create Parameter Panel widget
    - Create ParameterPanel class (QWidget)
    - Use QFormLayout for automatic label alignment
    - Add QComboBox for shape type selection
    - Add QComboBox for generator type selection
    - Add "Update Shape" button
    - Add "Generate Infill" button
    - Write test to verify panel can be created with correct widgets
    - _Requirements: 5, 6, 6.1, 7_
  - [ ] 8.2 Implement dynamic parameter forms
    - Create shape parameter form widgets (QDoubleSpinBox, QSpinBox)
    - Create generator parameter form widgets
    - Show/hide widgets based on selected type
    - Display unit suffixes (cm, kg, °)
    - Load default values from Hydra config
    - Write test to verify widgets show/hide correctly on type change
    - _Requirements: 5, 6, 6.1, 10_
  - [ ] 8.3 Implement parameter validation and error display
    - Connect to Pydantic validation
    - Display inline error messages for invalid inputs
    - Disable buttons during operations
    - Write test to verify validation errors are displayed correctly
    - _Requirements: 5, 9.2_

- [ ] 9. Implement Presentation Layer - Viewport
  - [ ] 9.1 Create Viewport widget (QGraphicsView)
    - Create ViewportWidget class using QGraphicsView/QGraphicsScene
    - Implement zoom with mouse wheel (centered on cursor)
    - Implement pan with mouse drag
    - Set up performance optimizations (viewport update mode, caching)
    - Write test to verify viewport can be created and basic operations work
    - _Requirements: 7, 7.2_
  - [ ] 9.2 Implement frame rendering
    - Render frame rods as QGraphicsLineItem objects
    - Use distinct color for frame
    - Update on shape changes
    - Write test to verify frame rods are rendered correctly
    - _Requirements: 7, 7.1_
  - [ ] 9.3 Implement infill rendering
    - Render infill rods as QGraphicsLineItem objects
    - Use layer-specific colors
    - Update on generation completion and best result updates
    - Write test to verify infill rods are rendered with correct colors
    - _Requirements: 7, 9.1.1_
  - [ ] 9.4 Implement rod enumeration display
    - Create enumeration markers (circles for infill, squares for frame)
    - Add counter numbers to markers
    - Draw dashed anchor lines connecting markers to rods
    - Position markers outside frame to minimize obstruction
    - Toggle visibility based on View menu action
    - Write test to verify enumeration markers are created correctly
    - _Requirements: 7.3_
  - [ ] 9.5 Implement part highlighting
    - Highlight selected rod when BOM table row is selected
    - Use distinct visual style for highlighted parts
    - Write test to verify highlighting works correctly
    - _Requirements: 8.1_

- [ ] 10. Implement Presentation Layer - BOM Table
  - [ ] 10.1 Create BOM Table widget (QTableWidget with QTabWidget)
    - Create BOMTableWidget class
    - Add two tabs: Frame Parts, Infill Parts
    - Set up columns: ID, Length (cm), Start Angle (°), End Angle (°), Weight (kg)
    - Enable column sorting
    - Write test to verify table structure is created correctly
    - _Requirements: 8_
  - [ ] 10.2 Implement BOM data population
    - Populate frame parts table from shape frame rods
    - Populate infill parts table from generation result
    - Use Rod.to_bom_entry() method
    - Update on shape changes and generation completion
    - Write test to verify data is populated correctly from rods
    - _Requirements: 8_
  - [ ] 10.3 Implement BOM totals calculation
    - Calculate and display per-tab totals (sum length, sum weight)
    - Calculate and display combined totals
    - Update totals when data changes
    - Write test to verify totals are calculated correctly
    - _Requirements: 8_
  - [ ] 10.4 Implement BOM row selection
    - Connect row selection to viewport highlighting
    - Emit signals when selection changes
    - Write test to verify selection signals are emitted correctly
    - _Requirements: 8.1_

- [ ] 11. Implement Presentation Layer - Progress Dialog
  - [ ] 11.1 Create Progress Dialog (QDialog)
    - Create ProgressDialog class (modal QDialog)
    - Add progress indicator (text or QProgressBar)
    - Add metrics display (iteration, fitness, elapsed time)
    - Add QTextEdit for progress logs
    - Add Cancel button
    - Write test to verify dialog can be created with correct widgets
    - _Requirements: 9.1, 9.1.1_
  - [ ] 11.2 Connect to generation signals
    - Connect to progress_updated signal for metrics updates
    - Connect to best_result_updated signal for viewport updates
    - Connect to generation_completed signal to close dialog
    - Connect to generation_failed signal to show error
    - Connect Cancel button to cancel_generation()
    - Throttle updates to max every 100ms
    - Write test to verify signals are connected and throttling works
    - _Requirements: 9.1, 9.1.1_

- [ ] 12. Implement Infrastructure Layer - File I/O with tests
  - [ ] 12.1 Implement save functionality with tests
    - Serialize parameters to JSON
    - Serialize infill geometry to JSON using Pydantic
    - Render viewport to PNG with configurable resolution
    - Export BOM tables to CSV
    - Create .rig.zip archive with all files
    - Write unit tests for save (ZIP structure, JSON format, file contents)
    - _Requirements: 8.2_
  - [ ] 12.2 Implement load functionality with tests
    - Extract .rig.zip archive
    - Validate ZIP structure and JSON schema
    - Deserialize parameters from JSON
    - Deserialize infill geometry using Pydantic
    - Restore UI state
    - Write unit tests for load (validation, deserialization, error handling)
    - Write integration tests for save/load round-trip
    - _Requirements: 8.2_
  - [ ] 12.3 Implement DXF export with tests
    - Use ezdxf library
    - Create separate layers for frame and infill
    - Export each rod as LINE entity
    - Use centimeters as units
    - Write unit tests for DXF export (layer structure, entity accuracy)
    - _Requirements: 8.2.1_

- [ ] 13. Implement Infrastructure Layer - Configuration Management
  - [ ] 13.1 Set up Hydra configuration loading
    - Create main `conf/config.yaml`
    - Register all dataclass configs with ConfigStore
    - Implement Hydra initialization in app.py
    - Write test to verify Hydra can load all config files correctly
    - _Requirements: 10_
  - [ ] 13.2 Implement QSettings for user preferences
    - Create hybrid config system (Hydra + QSettings)
    - Save/load window geometry and state
    - Save/load last used types and parameters
    - Implement preference override logic
    - Write test to verify QSettings save/load works correctly
    - _Requirements: 8.2.2_
  - [ ] 13.3 Create UI settings configuration
    - Create `conf/ui/settings.yaml` with colors and PNG resolution
    - Write test to verify UI settings can be loaded
    - _Requirements: 7, 10_

- [x] 14. Implement Infrastructure Layer - Logging
  - [x] 14.1 Set up logging system
    - Configure RichHandler for console output
    - Configure file handler with date-based filenames
    - Set up hierarchical logger structure
    - Implement --verbose flag for console logging
    - Write tests for logging configuration (COMPLETED)
    - _Requirements: 11_
  - [x] 14.2 Create logging configuration
    - Create `conf/logging/config.yaml` with logger hierarchy and levels
    - _Requirements: 11_

- [ ] 15. Integration and polish
  - [ ] 15.1 Wire all components together
    - Connect ApplicationController to UI components
    - Connect all signals and slots
    - Ensure proper event flow through all layers
    - Write integration tests for complete workflows (create, generate, save, load)
    - _Requirements: All_
  - [ ] 15.2 Implement error handling
    - Add try-catch blocks for validation errors
    - Add error dialogs for file I/O errors
    - Add error handling for generation failures
    - Log all errors with stack traces
    - Write tests to verify error handling works correctly
    - _Requirements: All_
  - [x] 15.3 Add CLI support
    - Implement Typer CLI with --debug and --verbose flags
    - Support --config-path for custom config directory
    - (COMPLETED in Task 1)
    - _Requirements: 11_
  - [ ] 15.4 Performance optimization
    - Verify QGraphicsView optimizations are applied
    - Test with large rod counts (100+ rods)
    - Optimize signal throttling if needed
    - Write performance tests to verify optimization targets are met
    - _Requirements: 9.1_

- [ ]* 16. Additional UI testing with pytest-qt
  - [ ]* 16.1 Write UI tests for parameter panel
    - Test dynamic widget visibility on type selection
    - Test validation error display
    - Test button enable/disable states
    - _Requirements: 5, 6, 9.2_
  - [ ]* 16.2 Write UI tests for viewport
    - Test rendering accuracy
    - Test zoom and pan functionality
    - Test highlighting behavior
    - _Requirements: 7, 7.2, 8.1_
  - [ ]* 16.3 Write UI tests for BOM table
    - Test data population accuracy
    - Test totals calculation
    - Test row selection behavior
    - _Requirements: 8, 8.1_
  - [ ]* 16.4 Write UI tests for progress dialog
    - Test signal handling
    - Test cancellation behavior
    - Test real-time updates
    - _Requirements: 9.1, 9.1.1_

## Notes

- Tasks marked with `*` are optional (advanced UI testing with pytest-qt)
- **EVERY task includes at least one test** - tests are part of implementation, not separate tasks
- Each task should be completed and tested before moving to the next
- Tests should be written immediately after (or alongside) the implementation
- All code should be integrated as it's developed (no orphaned code)
- Follow the Python standards defined in `.kiro/steering/python-standards.md`
- Refer to `.kiro/specs/railing-infill-generator/design.md` for detailed implementation guidance

### Task Workflow (CRITICAL)

#### Before Starting a Task:
1. Run: `uv run pytest --cov=railing_generator --cov-report=term-missing`
2. Note the TOTAL coverage % (e.g., "Starting coverage: 51%")
3. This is your baseline - you must maintain or improve it

#### During Development:
```bash
# Quick check after every code change
uv run mypy src/ && uv run ruff check . && uv run pytest --cov=railing_generator --cov-report=term-missing
```

#### Before Completing a Task:
1. Run coverage again
2. **REQUIREMENT**: New coverage MUST be >= baseline coverage
3. If coverage dropped, add more tests
4. Note final coverage (e.g., "Ending coverage: 58%")
5. All checks must pass: mypy ✅ ruff ✅ pytest ✅ coverage ✅

**Example:**
```
Task 2.1: Implement Rod class
- Starting coverage: 51%
- Ending coverage: 58% ✅
```

## Testing Approach

This plan follows an **implementation-first with immediate testing** approach:
- **Every task includes at least one test** to verify the implementation
- Core functionality is implemented first, then immediately tested
- Unit tests verify individual components work correctly
- Integration tests verify component interactions
- Only advanced UI tests with pytest-qt are marked as optional
- This ensures code quality while maintaining development momentum
- Tests are never standalone tasks - they are always part of the implementation task
