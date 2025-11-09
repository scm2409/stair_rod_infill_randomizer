# Design Document

## Overview

The Railing Infill Generator is a desktop application that generates rod arrangements for railing frames. Users define a railing frame shape (stair or rectangular), configure generation parameters, and the application generates infill patterns using various generation algorithms. The design emphasizes extensibility, allowing new shapes and generation algorithms to be added without modifying existing code.

### Key Design Goals

1. **Extensibility**: Support adding new shape types and generator algorithms through plugin architecture
2. **Quality**: Generate aesthetically pleasing arrangements with uniform hole distribution
3. **Performance**: Complete generation within 60 seconds for typical cases
4. **Usability**: Provide real-time visual feedback during generation
5. **Maintainability**: Clear separation of concerns with well-defined interfaces

## Architecture

### Layered Architecture

The application uses a four-layer architecture with clear boundaries:

```
┌─────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                        │
│                                                             │
│  • Main Window & UI Components                              │
│  • Vector Viewport (zoom, pan, rendering)                   │
│  • Parameter Panels (dynamic based on selection)            │
│  • BOM Tables & Progress Dialogs                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                         │
│                                                             │
│  • Application Controller (orchestrates workflows)          │
│  • Project State Management                                 │
│  • UI Event Handlers                                        │
│  • Signal/Slot Connections                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                            │
│                                                             │
│  • Shape System (frame geometry & validation)               │
│  • Generator System (infill creation algorithms)            │
│  • Geometry (Shapely: Point, LineString, Polygon)           │
│  • Rod (unified data structure for frame & infill)          │
│  • Quality Evaluator (for generators that need it)          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                       │
│                                                             │
│  • Configuration Management (Hydra)                         │
│  • File I/O (save/load .rig.zip)                           │
│  • Export (DXF, CSV, PNG)                                   │
│  • Logging System                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Design Patterns

**Strategy Pattern**: Used for shapes and generators to allow runtime selection of algorithms

**Factory Pattern**: Creates shape and generator instances based on type strings

**Observer Pattern**: UI components observe generation progress for real-time updates

**Repository Pattern**: Configuration management abstracts data access

## Core Concepts

### 1. Shape System

Shapes define the railing frame boundary where infill rods can be anchored.

**Shape Responsibilities:**
- Define frame geometry (boundary polygon, frame rods)
- Validate dimensional parameters
- Provide frame rods for anchoring (infill rods can connect anywhere along frame rod geometries)
- Frame rods include BOM information (length, angles, weight)

**Shape Types:**
- **Stair Shape**: Two vertical posts connected by angled handrail at top and stepped bottom
- **Rectangular Shape**: Simple rectangular frame
- **Future**: Curved, custom polygon shapes

**Key Abstractions:**
- All shapes implement common `Shape` interface
- Each shape has its own parameter class
- Shapes are immutable once created
- Factory creates shapes from type + parameters

### 2. Generator System

Generators create infill rod arrangements within a shape boundary.

**Generator Responsibilities:**
- Generate rod arrangements respecting constraints
- Organize rods into layers (layer organization rules vary by generator)
- Iterate until quality threshold met or limits reached (for iterative generators)
- Emit signals for progress updates (using PySide6 Signal/Slot)

**Generator Types:**
- **Random Generator**: Iterative random placement with fitness-based quality evaluation
- **Future**: Pattern-based (deterministic), ML-based, user-guided generators

**Generation Process (varies by generator type):**

*Random Generator Process:*
1. Select random positions along frame boundary for rod anchoring (using Shapely LineString.interpolate, respecting min distance constraint)
2. Generate rods with random angles (deviation from vertical within configured limit)
3. Ensure no crossings within same layer (using Shapely LineString.intersects)
4. Evaluate fitness score using Quality Evaluator
5. Keep best arrangement, repeat until acceptable or limit reached

**Shapely Operations Used:**
- `LineString.interpolate()` - Select random anchor points along frame
- `LineString.intersects()` - Check for rod crossings within layers
- `Point.distance()` - Enforce minimum anchor distance constraint

*Other generators may use different approaches* (e.g., deterministic algorithms, pre-defined patterns)

**Key Abstractions:**
- All generators inherit from QObject and implement common `Generator` interface
- Each generator has its own parameter class
- Generators emit signals for progress updates (type-safe)
- Generators can be cancelled via signal

### 3. Quality Evaluator (Optional Component)

The evaluator is used by generators that need quality assessment (e.g., Random Generator). It scores infill arrangements using multiple weighted criteria.

**Evaluation Criteria:**
1. **Hole Uniformity**: Prefer arrangements where all holes have similar area
2. **Incircle Uniformity**: Prefer uniform incircle radii across holes
3. **Angle Distribution**: Penalize rods too vertical or too angled
4. **Anchor Spacing**: Prefer evenly distributed rod connection positions along frame boundary
   - Uses separate weighting for horizontal elements (top/bottom) vs vertical elements (posts)
   - Configurable factor between horizontal and vertical anchor spacing importance
   - Allows different aesthetic/structural priorities for different frame orientations

**Fitness Calculation:**
- Each criterion produces score 0-1 (1 = perfect)
- Scores combined using configurable weights
- Final fitness = weighted sum of criteria
- Arrangement rejected if any hole exceeds max area

**Key Abstractions:**
- Used by generators that require quality assessment
- Criteria weights configurable in config files
- Evaluator is stateless and reusable
- Not all generators need an evaluator (e.g., deterministic generators)

### 4. Multi-Layer System

Infill rods are organized into layers. Layer organization rules depend on the generator.

**Random Generator Layer Rules:**
- Rods within same layer cannot cross
- Rods in different layers can cross
- Default: 2 layers
- Each layer rendered in different color

**Other Generators:**
- May use different layer organization strategies
- Some generators may allow crossings within layers
- Layer count and rules are generator-specific

**Benefits:**
- Allows denser infill patterns
- More design flexibility
- Easier manufacturing (layers = assembly steps)

## Component Design

### Domain Layer

#### Core Data Structures

**Rod Class** (Pydantic BaseModel)

Unified representation for both frame and infill rods using Shapely geometry and Pydantic.

**Core Fields (with validation):**
- `geometry: LineString` - Shapely LineString representing rod geometry
- `start_cut_angle_deg: float` - Cut angle at start (constrained: -90° to 90°)
- `end_cut_angle_deg: float` - Cut angle at end (constrained: -90° to 90°)
- `weight_kg_m: float` - Material density kg/m (must be positive)
- `layer: int` - Layer assignment (0 for frame, ≥1 for infill, must be ≥0)

**Computed Fields (Pydantic @computed_field):**
- `length_cm` - Computed from geometry.length
- `weight_kg` - Computed from length and material density
- `start_point` - Starting point from geometry (Shapely Point)
- `end_point` - Ending point from geometry (Shapely Point)

**Methods:**
- `model_dump()` - Serialize to dictionary (includes computed fields)
- `model_dump_json()` - Serialize directly to JSON string
- `model_validate(data)` - Deserialize from dictionary with validation
- `to_bom_entry(rod_id)` - Generate BOM table row

**Usage:**
- Frame rods: Created by Shape classes, layer = 0
- Infill rods: Created by Generator classes, layer ≥ 1
- Automatic validation on instantiation
- BOM generation: Both frame and infill use same method
- Serialization: Pydantic handles all serialization/deserialization

**Benefits:**
- Leverages Shapely for robust geometry operations
- Pydantic provides automatic validation with clear error messages
- Computed fields automatically included in serialization
- Field constraints (ge, le, gt) enforce valid values
- Type-safe rod handling throughout application
- Simplified serialization (no manual to_dict/from_dict needed)
- Consistent format for save/load operations
- Access to Shapely's geometry methods (intersects, distance, etc.)

#### Shape Components

**Shape Interface**
- `get_boundary()` → Shapely Polygon defining frame boundary
- `get_frame_rods()` → List of Rod objects representing frame (layer = 0)
  - Rod geometry can be accessed via `rod.geometry` for anchor point selection
  - Rods can anchor anywhere along frame rod geometries

**Shape Parameters** (Pydantic BaseModel)
- Each shape has a Pydantic model for parameters
- Validation rules defined using `@field_validator` decorators
- Automatic validation on instantiation
- Clear error messages for invalid values
- UI can catch `ValidationError` and display field-specific errors

**StairShape**
- Parameters (Pydantic model): post_length_cm, stair_height_cm, num_steps, frame_weight_kg_m
- Geometry: 2 vertical posts + angled handrail + stepped bottom
- Validation (via Pydantic validators):
  - post_length_cm > 0
  - stair_height_cm > 0
  - 1 ≤ num_steps ≤ 50
  - frame_weight_kg_m > 0

**RectangularShape**
- Parameters (Pydantic model): width_cm, height_cm, frame_weight_kg_m
- Geometry: 4 straight lines forming rectangle
- Validation (via Pydantic validators):
  - width_cm > 0
  - height_cm > 0
  - frame_weight_kg_m > 0

#### Generator Components

**Generator Interface**
- `generate(shape, params)` → InfillResult (emits signals during execution)
- Signals: `progress_updated`, `best_result_updated`, `generation_completed`, `generation_failed`

**Generator Parameters** (Pydantic BaseModel)
- Each generator has a Pydantic model for parameters
- Validation rules defined using `@field_validator` decorators
- Automatic validation on instantiation
- UI can catch `ValidationError` and display field-specific errors

**RandomGenerator** (uses Quality Evaluator)
- Parameters (Pydantic model): num_rods, max_rod_length_cm, max_angle_deviation_deg, num_layers, min_anchor_distance_cm, max_iterations, max_duration_sec
- Validation (via Pydantic validators):
  - num_rods > 0
  - max_rod_length_cm > 0
  - 0 ≤ max_angle_deviation_deg ≤ 90
  - num_layers ≥ 1
  - min_anchor_distance_cm ≥ 0
  - max_iterations > 0
  - max_duration_sec > 0
- Algorithm: Iterative random generation with fitness evaluation
- Termination: Acceptable fitness OR max iterations OR max duration OR user cancel
- Requires: QualityEvaluator instance

**Future Generator Examples:**
- **PatternGenerator**: Deterministic pattern-based (no iteration, no evaluator)
- **MLGenerator**: ML model-based (may or may not use evaluator)

**InfillResult** (Pydantic BaseModel)
- `rods: list[Rod]` - List of Rod objects with layer assignments
- `fitness_score: float | None` - Optional fitness score (for generators using evaluator)
- `iteration_count: int | None` - Optional iteration count (for iterative generators)
- `duration_sec: float | None` - Optional generation duration
- Immutable once created (Pydantic frozen=True)
- Automatic serialization via `model_dump()` and `model_dump_json()`
- Rods automatically serialized (Pydantic handles nested models)
- BOM entries generated via `Rod.to_bom_entry()` for each rod

#### Quality Evaluator (Used by Random Generator)

**QualityEvaluator**
- Input: rod arrangement, shape, parameters
- Output: fitness score (higher = better)
- Methods: evaluate(), is_acceptable()
- Usage: Optional component, only used by generators that need quality assessment

**Evaluation Process:**
1. Identify all holes (Shapely Polygons between rods and frame using polygonize)
2. Calculate hole areas (Shapely Polygon.area) and incircle radii (using Polygon.minimum_rotated_rectangle)
3. Analyze rod angles and anchor spacing (using Shapely geometry operations)
4. Compute individual criterion scores
5. Combine using configured weights

**Shapely Operations Used:**
- `polygonize()` - Identify holes from rod arrangement
- `Polygon.area` - Calculate hole areas
- `Polygon.minimum_rotated_rectangle` - Approximate incircle calculations
- `LineString.intersects()` - Check rod crossings
- `LineString.distance()` - Calculate anchor spacing
- `Point.distance()` - Measure distances between anchors

### Application Layer

#### Application Controller

Central orchestrator managing application workflows.

**Responsibilities:**
- Create/load/save projects
- Coordinate shape updates
- Manage infill generation
- Handle file operations
- Track project state

**Key Methods:**
- `create_new_project()` - Reset to defaults
- `update_shape(type, params)` - Create new shape
- `generate_infill(type, params)` - Start generation in background thread
- `cancel_generation()` - Cancel ongoing generation
- `save_project(path)` - Save to .rig.zip
- `load_project(path)` - Load from .rig.zip
- `export_dxf(path)` - Export to DXF

#### Project State

Represents current project data.

**State Components:**
- Shape type and parameters
- Shape instance
- Generator type and parameters
- Infill result (if generated)
- File path and modified flag

**State Management:**
- Immutable updates (create new state)
- Modified flag tracks unsaved changes
- Used for window title display

### Presentation Layer

#### Main Window

Top-level window organizing UI components.

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Menu Bar: File | View | Help                           │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│  Parameter   │      Viewport                            │
│  Panel       │   (zoom, pan, render)                    │
│              │                                          │
│  - Shape     │                                          │
│  - Generator │                                          │
│  - Buttons   ├──────────────────────────────────────────┤
│              │                                          │
│              │  BOM Table (2 tabs: Frame | Infill)     │
│              │  - ID, Length, Start Angle, End Angle,  │
│              │    Weight                                │
│              │  - Totals: Per-tab and Combined          │
│              │                                          │
├──────────────┴──────────────────────────────────────────┤
│  Status Bar: Ready | File: project.rig.zip* | Rods: 50  │
└─────────────────────────────────────────────────────────┘
```

**Menu Structure:**
- File: New, Open, Save, Save As, Export DXF, Quit
- View: Toggle Enumeration, Fit to View
- Help: About

#### Viewport Widget

Vector-based rendering of frame and infill.

**Features:**
- Zoom with mouse wheel (centered on cursor)
- Pan with mouse drag
- Render frame in distinct color
- Render infill with layer colors
- Optional rod enumeration (circles for infill, squares for frame, dashed anchor lines)
- Part highlighting on BOM selection

**Rendering Strategy:**
- Use QGraphicsScene for vector graphics
- Cache rendered items for performance
- Update only changed elements
- Lazy rendering for large designs

#### Parameter Panel

Dynamic form for shape and generator parameters.

**Behavior:**
- Show only relevant parameters for selected type
- Load defaults from configuration
- Validate on input
- Emit signals on changes
- Disable during operations

**Controls:**
- Dropdowns for type selection
- Number inputs for dimensions
- "Update Shape" button (short operation)
- "Generate Infill" button (long operation)

#### BOM Table Widget

Displays parts list with totals.

**Structure:**
- Two tabs: Frame Parts, Infill Parts
- Columns: ID, Length, Start Angle, End Angle, Weight
- Per-tab totals: Sum Length, Sum Weight
- Combined totals: Total Length, Total Weight

**Interaction:**
- Select row → highlight part in viewport
- Sortable columns
- Export to CSV (via save function)

#### Progress Dialog

Modal dialog for long-running operations.

**Display:**
- Progress information (generator-specific, e.g., iteration number for Random Generator)
- Quality metrics (if applicable, e.g., fitness score for Random Generator)
- Elapsed duration
- Progress logs text window
- Cancel button

**Behavior:**
- Blocks main window input
- Updates viewport with best result in real-time
- Closes on completion or cancel
- Returns best result found if cancelled

### Infrastructure Layer

#### Configuration Management

Uses Hydra for hierarchical configuration.

**Configuration Structure:**
```
conf/
├── config.yaml              # Main config
├── shapes/
│   ├── stair.yaml          # Stair defaults
│   └── rectangular.yaml    # Rectangular defaults
├── generators/
│   └── random.yaml         # Random generator defaults
├── evaluator/
│   └── criteria.yaml       # Quality criteria (for generators that use evaluator)
├── ui/
│   └── settings.yaml       # UI settings (colors, PNG resolution)
└── logging/
    └── config.yaml         # Logger hierarchy and levels
```

**Configuration Loading:**
- Loaded at startup via Hydra
- Type-safe access via Pydantic models
- Hydra configs converted to Pydantic parameter models
- Automatic validation on config load
- Clear error messages for invalid config values

**Pydantic + Hydra Integration:**
- Hydra loads YAML configs into dictionaries
- Dictionaries passed to Pydantic models for validation
- Pydantic raises `ValidationError` if config is invalid
- UI parameter panels use same Pydantic models
- Consistent validation between config files and UI input

#### File Management

Handles project persistence and export.

**Save Format (.rig.zip):**
- `parameters.json` - All shape/generator parameters
- `infill_geometry.json` - Rod coordinates and layers (if generated)
- `preview.png` - Viewport screenshot
- `frame_bom.csv` - Frame parts table
- `infill_bom.csv` - Infill parts table (if generated)

**DXF Export:**
- Uses ezdxf library
- Separate layers: "FRAME" and "INFILL"
- Each rod as LINE entity
- Preserves dimensions in cm

#### Logging System

Hierarchical logging with file and console output.

**Logger Hierarchy:**
```
root (INFO)
├── railing.ui (INFO)
├── railing.domain
│   ├── shapes (INFO)
│   ├── generators (DEBUG)
│   └── evaluator (DEBUG)
└── railing.application (INFO)
```

**Log Configuration:**
- File: `logs/railing_YYYY-MM-DD.log`
- Console: Only if `--verbose` flag
- Levels configurable per logger in config
- Rich formatting for console output

## Data Flow

### Shape Update Flow

```
User selects shape type
    ↓
Parameter panel updates to show relevant fields
    ↓
User enters parameters
    ↓
User clicks "Update Shape"
    ↓
Application validates parameters
    ↓
Application creates shape instance
    ↓
Viewport renders frame
    ↓
BOM table updates with frame parts
```

### Infill Generation Flow

```
User configures generator parameters
    ↓
User clicks "Generate Infill"
    ↓
Application validates parameters
    ↓
Progress dialog opens
    ↓
Generator runs in QThread:
    ├── Execute generation algorithm (varies by generator type)
    ├── For Random Generator:
    │   ├── Generate random arrangement
    │   ├── Evaluate fitness
    │   ├── Update best if improved
    │   └── Check termination conditions
    ├── Emit progress_updated signal → updates progress dialog
    ├── Emit best_result_updated signal → updates viewport (if applicable)
    └── Complete when done
    ↓
Progress dialog closes
    ↓
Viewport shows final result
    ↓
BOM table updates with infill parts
```

### Save/Load Flow

```
User clicks Save/Save As
    ↓
File dialog for location
    ↓
Application creates ZIP archive:
    ├── Serialize parameters to JSON
    ├── Serialize infill geometry to JSON
    ├── Render viewport to PNG
    ├── Export BOM tables to CSV
    └── Add all to ZIP
    ↓
Mark project as saved
    ↓
Update window title
```

## Error Handling

### Error Categories

**Validation Errors**
- Invalid parameters (negative dimensions, etc.)
- Display: Red highlighting in parameter panel + tooltip
- Recovery: User corrects input

**Generation Errors**
- No valid arrangement found
- Display: Error message in progress dialog
- Recovery: Adjust parameters and retry

**File I/O Errors**
- Cannot read/write files
- Display: Modal error dialog
- Recovery: Choose different location or check permissions

**Unexpected Errors**
- Bugs, crashes
- Display: Generic error dialog
- Recovery: Log details, suggest restart

### Error Display Strategy

- Validation: Inline feedback (immediate)
- Operations: Progress dialog or modal (contextual)
- Critical: Modal dialog with details (blocking)
- All errors logged with stack traces

## Performance Considerations

### Generation Performance

**Target**: < 60 seconds for 1000 iterations

### UI Responsiveness

**Strategy**: Run generation in separate thread using QThread

**Implementation:**
- Generator runs in QThread (moveToThread pattern)
- Generator emits signals for progress updates
- UI connects to signals and updates accordingly
- Signals are thread-safe (Qt handles cross-thread communication)
- Update viewport max every 100ms using signal throttling
- Cancel via signal to generator thread

### Memory Management

**Considerations:**
- Only store best arrangement during generation
- Clear viewport scene when loading new project

## Testing Strategy

### Unit Tests

**Domain Layer:**
- Rod class (geometry operations, serialization, BOM generation)
- Shape implementations (boundary, validation, BOM, Shapely geometry)
- Generator logic (arrangement generation, layer organization, Shapely operations)
- Quality evaluator (fitness calculations, individual metrics, hole identification) - for Random Generator

**Infrastructure Layer:**
- File I/O (save/load, ZIP structure)
- DXF export (layer organization, entity creation)
- Configuration loading

### Integration Tests

**Cross-Layer:**
- Shape + Generator integration
- Generator + Evaluator integration
- Application controller workflows
- End-to-end save/load cycle

### UI Tests

**Presentation Layer:**
- Parameter panel updates on type selection
- Viewport rendering accuracy
- BOM table calculations
- Progress dialog behavior

### Test Data

- Predefined shape configurations
- Known-good infill arrangements
- Edge cases (minimum/maximum parameters)
- Invalid inputs for validation testing

## Security Considerations

- Validate ZIP file structure before extraction
- Sanitize file paths (prevent directory traversal)
- Validate JSON schema on load
- Limit file sizes for imports
- Range-check all numeric parameters

## Deployment

### Package Structure

```
railing-generator/
├── src/
│   └── railing_generator/
│       ├── __main__.py
│       ├── app.py
│       ├── domain/
│       ├── application/
│       ├── presentation/
│       └── infrastructure/
├── conf/
├── tests/
├── pyproject.toml
└── README.md
```

### Dependencies

- PySide6 (UI framework)
- pydantic (parameter validation and data models)
- hydra-core (configuration)
- omegaconf (config objects)
- rich (logging)
- typer (CLI)
- shapely (geometry and geometry calculations)
- numpy (when shapely is not enough)
- ezdxf (DXF export)

### Entry Point

Command-line interface with options:
- `-d, --debug`: Enable debug logging
- `-v, --verbose`: Log to stdout
- `--config-path`: Custom config directory

## Future Enhancements

- Additional shape types (curved, custom polygons)
- Additional generator types (pattern-based, ML-based)
- Undo/redo functionality
- 3D visualization
- Material cost calculation
- Recent files list
- Optimal cutting plan for manufacturing

## PySide6 Framework Integration

### Overview

PySide6 provides the Qt framework bindings for Python, offering a comprehensive set of tools perfectly suited for this application. This section details which PySide6 components will be used and why they fit the design.

### Core Components Used

#### 1. QGraphicsView / QGraphicsScene (Vector Viewport)

**Why it fits:**
- Native vector graphics rendering (perfect for line-based designs)
- Built-in zoom and pan support
- Efficient scene graph for thousands of items
- Hardware-accelerated rendering
- Easy coordinate transformations

**Usage in design:**
- Main viewport for displaying frame and infill
- QGraphicsScene holds all geometric items (lines, markers)
- QGraphicsView provides zoom/pan interaction
- Custom QGraphicsItem subclasses for enumeration markers

**Key features:**
- `QGraphicsScene.addLine()` - Add frame and infill lines
- `QGraphicsView.wheelEvent()` - Mouse wheel zoom
- `QGraphicsView.setTransform()` - Zoom centered on cursor
- `QGraphicsScene.changed` signal - React to scene updates
- `QGraphicsItem.setZValue()` - Layer ordering (frame vs infill)

#### 2. Signal/Slot Mechanism (Progress Updates)

**Why it fits:**
- Type-safe event handling
- Thread-safe cross-thread communication
- Decoupled architecture
- Built into Qt's event system
- No callback complexity

**Usage in design:**
- Generator emits `progress_updated(int, float, float)` signal
- Generator emits `best_result_updated(InfillResult)` signal
- UI connects to signals for real-time updates
- Automatic queued invocation across threads

**Key features:**
- `Signal(int, float, float)` - Typed signal definitions
- `@Slot(int, float, float)` - Typed slot decorators
- Automatic thread-safe delivery
- Connect/disconnect at runtime

#### 3. QThread (Background Generation)

**Why it fits:**
- Native threading support
- Integrates with Signal/Slot
- moveToThread pattern for worker objects
- Proper thread lifecycle management

**Usage in design:**
- Generator runs in separate QThread
- Emits signals for progress updates
- UI remains responsive during generation
- Clean cancellation via flag + signal

**Key features:**
- `QThread.start()` - Begin execution
- `QThread.quit()` - Graceful shutdown
- `QThread.wait()` - Block until finished
- `started` and `finished` signals
- `moveToThread()` - Move worker to thread

#### 4. QMainWindow (Application Structure)

**Why it fits:**
- Standard application window framework
- Built-in menu bar, status bar, dock widgets
- Splitter support for resizable panels
- Save/restore window state

**Usage in design:**
- Main application window
- Menu bar for File, View, Help
- Central widget with splitter layout
- Status bar for quick messages

**Key features:**
- `QMainWindow.menuBar()` - Menu system
- `QMainWindow.setCentralWidget()` - Main content
- `QSplitter` - Resizable panel layout
- `QMainWindow.statusBar()` - Status messages

**Status Bar Usage:**
- Left section: Current operation status ("Ready", "Generating...", "Saved")
- Right section: Quick stats (number of rods, quality metrics if available, etc.)

#### 5. QTableWidget (BOM Tables)

**Why it fits:**
- Built-in table display
- Sortable columns
- Selection handling
- Easy data population

**Usage in design:**
- Frame parts table
- Infill parts table
- Totals display
- Row selection → viewport highlighting

**Key features:**
- `QTableWidget.setItem()` - Populate cells
- `QTableWidget.setSortingEnabled()` - Column sorting
- `currentItemChanged` signal - Selection tracking
- `QTableWidget.horizontalHeader()` - Column headers

#### 6. QTabWidget (BOM Organization)

**Why it fits:**
- Simple tab interface
- Built-in tab switching
- Easy to add/remove tabs

**Usage in design:**
- Separate tabs for frame and infill BOM
- Clean organization of related data

**Key features:**
- `QTabWidget.addTab()` - Add tabs
- `currentChanged` signal - Tab switching
- `QTabWidget.setTabText()` - Tab labels

#### 7. QDialog (Progress Dialog)

**Why it fits:**
- Modal dialog support
- Built-in button handling
- Event loop integration

**Usage in design:**
- Progress dialog during generation
- Blocks main window input
- Shows metrics and logs
- Cancel button

**Key features:**
- `QDialog.exec()` - Modal execution
- `QDialog.reject()` - Cancel handling
- `QProgressBar` - Visual progress
- `QTextEdit` - Log display

#### 8. QFileDialog (File Operations)

**Why it fits:**
- Native file dialogs
- Filter support
- Recent locations
- Cross-platform

**Usage in design:**
- Save/Load project files
- Export DXF
- Native look and feel

**Key features:**
- `QFileDialog.getSaveFileName()` - Save dialog
- `QFileDialog.getOpenFileName()` - Open dialog
- File filters (*.rig.zip, *.dxf)
- Default directories

#### 9. QFormLayout / QVBoxLayout (Parameter Panel)

**Why it fits:**
- Automatic label alignment
- Responsive layout
- Easy to add/remove widgets
- Platform-native spacing

**Usage in design:**
- Parameter input forms
- Dynamic widget visibility
- Clean label/input pairing

**Key features:**
- `QFormLayout.addRow()` - Add label/widget pairs
- `QVBoxLayout.addWidget()` - Vertical stacking
- `QWidget.setVisible()` - Show/hide parameters
- Automatic layout management

#### 10. QDoubleSpinBox / QSpinBox (Numeric Input)

**Why it fits:**
- Built-in validation
- Min/max constraints
- Decimal precision control
- Keyboard and mouse input

**Usage in design:**
- All numeric parameters
- Automatic validation
- Unit suffixes (cm, kg, °)

**Key features:**
- `QDoubleSpinBox.setValue()` - Set value
- `QDoubleSpinBox.setRange()` - Min/max
- `QDoubleSpinBox.setSuffix()` - Unit display
- `valueChanged` signal - Value updates

#### 11. QComboBox (Type Selection)

**Why it fits:**
- Dropdown selection
- String or data items
- Current selection tracking

**Usage in design:**
- Shape type selection
- Generator type selection
- Triggers parameter panel updates

**Key features:**
- `QComboBox.addItem()` - Add options
- `QComboBox.currentText()` - Get selection
- `currentTextChanged` signal - Selection changes
- `QComboBox.setCurrentText()` - Set selection

#### 12. QAction (Menu Actions)

**Why it fits:**
- Unified action system
- Keyboard shortcuts
- Enable/disable state
- Icon support

**Usage in design:**
- File menu actions (New, Open, Save, etc.)
- View menu actions (Toggle Enumeration)
- Keyboard shortcuts (Ctrl+S, Ctrl+N)

**Key features:**
- `QAction.triggered` signal - Action invoked
- `QAction.setShortcut()` - Keyboard shortcut
- `QAction.setEnabled()` - Enable/disable
- `QAction.setIcon()` - Action icon

### Design Patterns with PySide6

#### Worker Thread Pattern

```
Main Thread                    Worker Thread
    │                               │
    ├─ Create QThread              │
    ├─ Create Worker (QObject)     │
    ├─ worker.moveToThread()  ────>│
    ├─ Connect signals             │
    ├─ thread.start()          ────>│
    │                               ├─ run()
    │                               ├─ emit progress_updated
    │<──── progress_updated ────────┤
    ├─ Update UI                    │
    │                               ├─ emit best_result_updated
    │<──── best_result_updated ─────┤
    ├─ Update viewport              │
    │                               ├─ emit finished
    │<──── finished ────────────────┤
    ├─ thread.quit()           ────>│
    └─ thread.wait()                └─ Exit
```

#### Model-View Pattern (BOM Tables)

- QTableWidget acts as both model and view (simplified)
- Data stored in table items
- Selection model for row selection
- Signals for selection changes
- Custom delegates possible for advanced rendering

#### Graphics View Framework

```
QGraphicsView (viewport widget)
    └─ QGraphicsScene (scene graph)
        ├─ QGraphicsLineItem (frame lines)
        ├─ QGraphicsLineItem (infill rods)
        ├─ QGraphicsEllipseItem (enumeration circles)
        ├─ QGraphicsRectItem (enumeration squares)
        └─ QGraphicsTextItem (enumeration numbers)
```

### Thread Safety Considerations

**Qt's Thread Safety Rules:**
1. GUI operations only in main thread
2. Signals automatically queued across threads
3. Use QMutex for shared data access
4. Worker objects live in worker thread

**Our Implementation:**
- Generator runs in QThread
- Emits signals (automatically queued)
- UI updates only in main thread (via slots)
- No shared mutable state between threads
- Cancellation via atomic flag

### Performance Optimizations

**QGraphicsView Optimizations:**
- `QGraphicsView.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)` - Efficient updates
- `QGraphicsScene.setItemIndexMethod(QGraphicsScene.NoIndex)` - For static scenes
- `QGraphicsItem.setCacheMode(QGraphicsItem.DeviceCoordinateCache)` - Cache rendering
- `QGraphicsView.setRenderHint(QPainter.Antialiasing, False)` - Faster rendering for many items

**Signal Throttling:**
- Emit progress signals max every 100ms
- Use QTimer for throttling
- Batch viewport updates

**Lazy Loading:**
- Only render visible items
- Use QGraphicsScene.itemsBoundingRect() for culling
- Defer enumeration rendering until toggled

### Testing with PySide6

**pytest-qt Plugin:**
- Provides `qtbot` fixture
- Simulate user interactions
- Wait for signals
- Test threading

**Example:**
```python
def test_generation_progress(qtbot):
    generator = RandomGenerator(evaluator)
    
    with qtbot.waitSignal(generator.progress_updated, timeout=1000):
        generator.generate(shape, params)
    
    assert generator.best_fitness > 0
```

## Configuration Management: Hybrid Approach

**Use both for different purposes:**

1. **Hydra for Application Defaults**
   - Shape default parameters
   - Generator default parameters
   - Quality evaluator criteria (for generators that use it)
   - UI settings (colors, resolution)
   - Logging configuration
   - Stored in `conf/` directory (version controlled)

2. **QSettings for User Preferences**
   - Window geometry and state
   - Recent files list
   - Last used shape/generator types
   - User-modified parameter values
   - UI preferences (panel sizes, etc.)
   - Stored in platform-specific location (not version controlled)

**Benefits of Hybrid:**
- Hydra provides powerful defaults and configuration system
- QSettings handles user-specific preferences naturally
- Clear separation: defaults vs user customization
- Best of both worlds

**Implementation:**
```python
class AppConfig:
    def __init__(self):
        # Load defaults from Hydra
        self.defaults = self._load_hydra_config()
        
        # Load user preferences from QSettings
        self.settings = QSettings("RailingGenerator", "RailingApp")
    
    def get_parameter(self, key: str, default=None):
        """Get parameter, preferring user setting over default"""
        # Check user settings first
        if self.settings.contains(key):
            return self.settings.value(key)
        
        # Fall back to Hydra defaults
        return self.defaults.get(key, default)
    
    def set_user_preference(self, key: str, value):
        """Save user preference"""
        self.settings.setValue(key, value)
```

## Project Structure

**Project structure:**
```
project-root/
├── src/
│   └── railing_generator/
│       ├── __main__.py
│       ├── app.py
│       ├── domain/
│       ├── application/
│       ├── presentation/        # UI layer
│       └── infrastructure/
├── conf/                        # Hydra configs
├── tests/
├── pyproject.toml
└── README.md
```

**Optional resources directory** (if needed for icons/images):
```
src/railing_generator/
└── resources/
    ├── icons/
    └── resources.qrc
```

**Entry point structure**:
```python
# src/railing_generator/__main__.py
import sys
from PySide6.QtWidgets import QApplication
from railing_generator.app import main

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = main()
    main_window.show()
    sys.exit(app.exec())
```

### Deployment Considerations

**For PySide6 applications:**

1. **Use pyside6-deploy** (recommended):
   - Creates standalone executables
   - Handles Qt dependencies automatically
   - Generates `pysidedeploy.spec` config

2. **Or use PyInstaller/Nuitka**:
   - More control over packaging
   - Requires manual Qt plugin configuration

3. **Include in pyproject.toml**:
```toml
[project.scripts]
railing-generator = "railing_generator.__main__:main"

[tool.briefcase]
# For cross-platform deployment
```

**Configuration approach:**
- Hydra for application configuration (defaults, presets)
- QSettings for user preferences (window state, recent files)
- Hybrid approach leverages strengths of both systems

### Development Workflow

**With all technologies integrated:**

1. **Development:**
   ```bash
   # Run with debug logging and verbose console output
   uv run railing-generator --debug --verbose
   ```

2. **Type checking:**
   ```bash
   # mypy validates Qt types and Signal/Slot signatures
   uv run mypy src/
   ```

3. **Testing:**
   ```bash
   # pytest-qt for GUI testing
   uv run pytest
   ```

4. **Production:**
   ```bash
   # Clean GUI without console output
   railing-generator
   ```

**All technologies complement each other perfectly and are commonly used together in professional PySide6 applications.**

## Pydantic Usage Throughout Application

Pydantic is used extensively for data validation, serialization, and computed fields:

### 1. Parameter Models
- **ShapeParameters** (StairShapeParameters, RectangularShapeParameters)
  - Field validation with `@field_validator`
  - Constraints using `Field(gt=0, ge=0, le=90, etc.)`
  - Used by both Hydra config loading and UI input
  - Automatic validation with clear error messages

- **GeneratorParameters** (RandomGeneratorParameters, etc.)
  - Same validation approach as shape parameters
  - Consistent validation across config and UI

### 2. Data Models
- **Rod** (BaseModel)
  - Core data structure for frame and infill rods
  - Computed fields: `length_cm`, `weight_kg`, `start_point`, `end_point`
  - Field constraints for angles and weights
  - Custom serialization for Shapely geometry
  - Automatic serialization/deserialization

- **InfillResult** (BaseModel)
  - Contains list of Rod objects
  - Optional fields for fitness, iteration count, duration
  - Immutable (frozen=True)
  - Automatic nested model serialization

### 3. Configuration Integration
- Hydra loads YAML → dict
- Dict passed to Pydantic models for validation
- ValidationError raised if config invalid
- Same models used for UI parameter panels

### 4. Serialization (Save/Load)
- `model_dump()` - Convert to dict for JSON serialization
- `model_dump_json()` - Direct JSON string output
- `model_validate()` - Deserialize with validation
- Computed fields automatically included
- Custom serializers for Shapely types

### 5. UI Integration
- UI catches `ValidationError` for inline error display
- Field-specific error messages shown in parameter panel
- Same validation logic as config files
- Real-time validation as user types

### Benefits
- **Single source of truth** for validation logic
- **Type-safe** throughout application (works with mypy)
- **Clear error messages** for users and developers
- **Automatic serialization** (no manual dict conversion)
- **Computed fields** eliminate redundant calculations
- **Field constraints** enforce valid values at model level

## Appendix: Code Examples

### Rod Class Example

```python
from typing import Any
from pydantic import BaseModel, Field, computed_field, field_serializer, ValidationError
from shapely.geometry import LineString, Point

class Rod(BaseModel):
    """
    Unified representation for frame and infill rods using Shapely geometry.
    Uses Pydantic for validation, serialization, and computed fields.
    """
    
    # Core fields with validation constraints
    geometry: LineString = Field(exclude=True)  # Excluded from default serialization
    start_cut_angle_deg: float = Field(ge=-90, le=90)  # Constrained to valid range
    end_cut_angle_deg: float = Field(ge=-90, le=90)
    weight_kg_m: float = Field(gt=0)  # Must be positive
    layer: int = Field(ge=0, default=0)  # 0 for frame, ≥1 for infill
    
    # Pydantic config to allow Shapely types
    model_config = {"arbitrary_types_allowed": True}
    
    @computed_field
    @property
    def length_cm(self) -> float:
        """Computed from geometry - automatically included in serialization"""
        return self.geometry.length
    
    @computed_field
    @property
    def weight_kg(self) -> float:
        """Computed from length and material density"""
        return (self.length_cm / 100.0) * self.weight_kg_m
    
    @computed_field
    @property
    def start_point(self) -> Point:
        """Get start point from geometry"""
        return Point(self.geometry.coords[0])
    
    @computed_field
    @property
    def end_point(self) -> Point:
        """Get end point from geometry"""
        return Point(self.geometry.coords[-1])
    
    @field_serializer('geometry', when_used='json')
    def serialize_geometry(self, geometry: LineString) -> dict[str, Any]:
        """Serialize LineString as coordinate pairs for JSON"""
        coords = list(geometry.coords)
        return {
            "start": {"x": coords[0][0], "y": coords[0][1]},
            "end": {"x": coords[-1][0], "y": coords[-1][1]}
        }
    
    def to_bom_entry(self, rod_id: int) -> dict[str, Any]:
        """Generate BOM table entry with rounded values"""
        return {
            "id": rod_id,
            "length_cm": round(self.length_cm, 2),
            "start_angle_deg": round(self.start_cut_angle_deg, 1),
            "end_angle_deg": round(self.end_cut_angle_deg, 1),
            "weight_kg": round(self.weight_kg, 3)
        }

# Usage examples:

# Create rod with automatic validation
rod = Rod(
    geometry=LineString([(0, 0), (100, 50)]),
    start_cut_angle_deg=45.0,
    end_cut_angle_deg=-30.0,
    weight_kg_m=0.5,
    layer=1
)

# Computed fields automatically available
print(rod.length_cm)  # Computed from geometry
print(rod.weight_kg)  # Computed from length and density

# Serialize to dict (for save/load) - includes computed fields
data = rod.model_dump()
json_str = rod.model_dump_json()  # Direct JSON serialization

# Deserialize from dict
rod2 = Rod.model_validate(data)

# Validation happens automatically on instantiation
try:
    invalid_rod = Rod(
        geometry=LineString([(0, 0), (100, 50)]),
        start_cut_angle_deg=100.0,  # Invalid! Must be -90 to 90
        end_cut_angle_deg=0.0,
        weight_kg_m=0.5
    )
except ValidationError as e:
    print(e)  # Clear error message about angle constraint
```

### Shape Interface Example

```python
from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel, field_validator
from shapely.geometry import Polygon

class ShapeParameters(BaseModel):
    """Base class for shape parameters with Pydantic validation"""
    pass

class StairShapeParameters(ShapeParameters):
    """Parameters for stair-shaped railing frame"""
    post_length_cm: float
    stair_height_cm: float
    num_steps: int
    frame_weight_kg_m: float
    
    @field_validator('post_length_cm', 'stair_height_cm', 'frame_weight_kg_m')
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Must be positive')
        return v
    
    @field_validator('num_steps')
    @classmethod
    def validate_num_steps(cls, v: int) -> int:
        if not 1 <= v <= 50:
            raise ValueError('Must be between 1 and 50')
        return v

class RectangularShapeParameters(ShapeParameters):
    """Parameters for rectangular railing frame"""
    width_cm: float
    height_cm: float
    frame_weight_kg_m: float
    
    @field_validator('width_cm', 'height_cm', 'frame_weight_kg_m')
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Must be positive')
        return v

class Shape(ABC):
    """Abstract base class for all railing frame shapes"""
    
    def __init__(self, params: ShapeParameters):
        """
        Initialize shape with validated parameters.
        Pydantic raises ValidationError if params are invalid.
        """
        self.params = params
    
    @abstractmethod
    def get_boundary(self) -> Polygon:
        """Returns the boundary polygon of the shape"""
        pass
    
    @abstractmethod
    def get_frame_rods(self) -> List[Rod]:
        """
        Returns frame rods (layer = 0)
        Rod geometry can be accessed via rod.geometry for anchor operations
        """
        pass
```

### Generator Interface Example

```python
from abc import ABC, abstractmethod
from PySide6.QtCore import QObject, Signal

class Generator(QObject, ABC):
    """Abstract base class for all infill generators"""
    
    # Signals for progress updates (type-safe)
    progress_updated = Signal(dict)  # progress_data (generator-specific)
    best_result_updated = Signal(object)  # InfillResult (optional, for iterative generators)
    generation_completed = Signal(object)  # InfillResult
    generation_failed = Signal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self._cancelled = False
    
    @abstractmethod
    def generate(
        self,
        shape: Shape,
        params: GeneratorParameters
    ) -> InfillResult:
        """
        Generates infill arrangement.
        Emits signals during generation for progress updates.
        Checks self._cancelled flag to support cancellation.
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, params: GeneratorParameters) -> bool:
        """Validates generator parameters"""
        pass
    
    def cancel(self):
        """Request cancellation of generation"""
        self._cancelled = True
```

### Generator Usage Example

```python
# In application controller
class GenerationWorker(QObject):
    """Worker that runs generator in separate thread"""
    
    finished = Signal(object)  # InfillResult
    
    def __init__(self, generator: Generator, shape: Shape, params: GeneratorParameters):
        super().__init__()
        self.generator = generator
        self.shape = shape
        self.params = params
    
    def run(self):
        """Execute generation (runs in QThread)"""
        result = self.generator.generate(self.shape, self.params)
        self.finished.emit(result)

# In UI
def start_generation(self):
    # Create thread and worker
    self.thread = QThread()
    self.worker = GenerationWorker(generator, shape, params)
    self.worker.moveToThread(self.thread)
    
    # Connect signals
    self.thread.started.connect(self.worker.run)
    self.worker.finished.connect(self.on_generation_complete)
    self.worker.finished.connect(self.thread.quit)
    generator.progress_updated.connect(self.on_progress_update)
    generator.best_result_updated.connect(self.on_best_result_update)
    
    # Start thread
    self.thread.start()

def cancel_generation(self):
    """Cancel ongoing generation"""
    self.worker.generator.cancel()
```

### Quality Evaluator Example

```python
class QualityEvaluator:
    """Evaluates quality of infill arrangements"""
    
    def evaluate(
        self,
        arrangement: List[Line],
        shape: Shape,
        params: GeneratorParameters
    ) -> float:
        """
        Calculates weighted fitness score
        Returns: fitness score (higher is better)
        """
        # Calculate individual metrics
        hole_uniformity = self._calculate_hole_uniformity(arrangement, shape)
        incircle_uniformity = self._calculate_incircle_uniformity(arrangement, shape)
        angle_quality = self._calculate_angle_quality(arrangement, params)
        
        # Anchor spacing with separate horizontal/vertical weighting
        anchor_spacing_horizontal = self._calculate_anchor_spacing_horizontal(arrangement, shape)
        anchor_spacing_vertical = self._calculate_anchor_spacing_vertical(arrangement, shape)
        
        # Weighted combination
        fitness = (
            self.criteria.hole_uniformity_weight * hole_uniformity +
            self.criteria.incircle_uniformity_weight * incircle_uniformity +
            self.criteria.angle_distribution_weight * angle_quality +
            self.criteria.anchor_spacing_horizontal_weight * anchor_spacing_horizontal +
            self.criteria.anchor_spacing_vertical_weight * anchor_spacing_vertical
        )
        
        return fitness
```

### Configuration Example

```yaml
# conf/generators/random.yaml
num_rods: 50
max_rod_length_cm: 200.0
max_angle_deviation_deg: 30.0
num_layers: 2
min_anchor_distance_cm: 10.0
infill_weight_kg_m: 0.5
max_iterations: 1000
max_duration_sec: 60.0
```

```yaml
# conf/evaluator/criteria.yaml
# Quality evaluation criteria weights (used by Random Generator)
hole_uniformity_weight: 0.3
incircle_uniformity_weight: 0.2
angle_distribution_weight: 0.2
anchor_spacing_horizontal_weight: 0.15  # Weight for top/bottom frame elements
anchor_spacing_vertical_weight: 0.15    # Weight for post frame elements

# Maximum allowed hole area (cm²) - arrangements exceeding this are rejected
max_hole_area_cm2: 500.0
```
