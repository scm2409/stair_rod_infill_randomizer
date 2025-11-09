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
│  • Geometry Primitives (Point, Line, Polygon)               │
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
- Define frame geometry (boundary polygon, frame lines)
- Validate dimensional parameters
- Provide boundary for rod anchoring (rods can connect anywhere along frame lines)
- Calculate frame BOM (length, angles, weight)

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
1. Select random positions along frame boundary for rod anchoring (respecting min distance constraint)
2. Generate rods with random angles (deviation from vertical within configured limit)
3. Ensure no crossings within same layer
4. Evaluate fitness score using Quality Evaluator
5. Keep best arrangement, repeat until acceptable or limit reached

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

#### Shape Components

**Shape Interface**
- `get_boundary()` → Polygon defining frame boundary
- `get_frame_lines()` → List of frame line segments (rods can anchor anywhere along these)
- `validate_parameters()` → Check parameter validity
- `calculate_bom()` → Generate frame parts list

**StairShape**
- Parameters: post_length_cm, stair_height_cm, num_steps, frame_weight_per_meter_kg_m
- Geometry: 2 vertical posts + angled handrail + stepped bottom
- Validation: Positive dimensions, reasonable step count

**RectangularShape**
- Parameters: width_cm, height_cm, frame_weight_per_meter_kg_m
- Geometry: 4 straight lines forming rectangle
- Validation: Positive dimensions

#### Generator Components

**Generator Interface**
- `generate(shape, params)` → InfillResult (emits signals during execution)
- `validate_parameters()` → Check parameter validity
- Signals: `progress_updated`, `best_result_updated`, `generation_completed`, `generation_failed`

**RandomGenerator** (uses Quality Evaluator)
- Parameters: num_rods, max_rod_length_cm, max_angle_deviation_deg, num_layers, min_anchor_distance_cm, max_iterations, max_duration_sec
- Algorithm: Iterative random generation with fitness evaluation
- Termination: Acceptable fitness OR max iterations OR max duration OR user cancel
- Requires: QualityEvaluator instance

**Future Generator Examples:**
- **PatternGenerator**: Deterministic pattern-based (no iteration, no evaluator)
- **MLGenerator**: ML model-based (may or may not use evaluator)

**InfillResult**
- Contains: rod list, layer organization
- Optional: fitness score (only for generators using evaluator), iteration count, duration
- Immutable once created

#### Quality Evaluator (Used by Random Generator)

**QualityEvaluator**
- Input: rod arrangement, shape, parameters
- Output: fitness score (higher = better)
- Methods: evaluate(), is_acceptable()
- Usage: Optional component, only used by generators that need quality assessment

**Evaluation Process:**
1. Identify all holes (polygons between rods and frame)
2. Calculate hole areas and incircle radii
3. Analyze rod angles and anchor spacing
4. Compute individual criterion scores
5. Combine using configured weights

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
- Optional line enumeration (circles for infill, squares for frame)
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
- Progress logs
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
- Command-line overrides supported
- Type-safe access via dataclasses

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

**Optimizations:**
- NumPy for geometry calculations (vectorized operations)
- Spatial indexing for collision detection (quadtree)
- Early termination when acceptable quality reached (for iterative generators)
- Efficient hole identification algorithm (for generators using evaluator)

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
- Compress geometry in save files (JSON)
- Limit log file size (rotation)

## Testing Strategy

### Unit Tests

**Domain Layer:**
- Geometry primitives (Point, Line, Polygon operations)
- Shape implementations (boundary, validation, BOM)
- Generator logic (arrangement generation, layer organization)
- Quality evaluator (fitness calculations, individual metrics) - for Random Generator

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
- hydra-core (configuration)
- omegaconf (config objects)
- rich (logging)
- typer (CLI)
- numpy (geometry calculations)
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
- Structural analysis integration
- Recent files list
- Keyboard shortcuts
- Print functionality

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
- Center section: Current file name with modified indicator (asterisk)
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

### Why PySide6 Over Alternatives

**vs PyQt6:**
- LGPL license (more permissive)
- Official Qt for Python project
- Better long-term support

**vs Tkinter:**
- Much richer widget set
- Better graphics support (QGraphicsView)
- Native threading integration
- Professional appearance

**vs Web-based (Electron, etc.):**
- Better performance
- Native look and feel
- Smaller distribution size
- Direct Python integration

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

## Integration of Other Technologies with PySide6

### Rich (RichHandler for Logging)

**Compatibility: Excellent ✓**

**Why it works well:**
- Rich is purely for console output (stdout/stderr)
- PySide6 GUI runs independently of console
- Perfect for CLI mode and development
- No conflicts with Qt's event system

**Integration approach:**
```python
import logging
from rich.logging import RichHandler

# Setup logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),  # Console output
        logging.FileHandler("logs/app.log")  # File output
    ]
)

# Works perfectly with PySide6
from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)
# Logging works in parallel with GUI
```

**Benefits:**
- Beautiful console output during development
- Rich tracebacks for debugging
- Progress bars can run alongside GUI (in terminal)
- No interference with Qt widgets

**Considerations:**
- Rich output only visible if app launched from terminal
- Use `--verbose` flag to enable console logging
- File logging always works regardless

**Verdict: Keep Rich** - Perfect for development and CLI debugging

### Typer (CLI Parsing)

**Compatibility: Excellent ✓**

**Why it works well:**
- Typer handles CLI parsing before GUI starts
- Clean separation: CLI → parse args → launch GUI
- Common pattern in Qt applications
- No runtime conflicts

**Integration approach:**
```python
# src/railing_generator/__main__.py
import typer
from PySide6.QtWidgets import QApplication
from railing_generator.presentation.main_window import MainWindow

app = typer.Typer()

@app.command()
def main(
    debug: bool = typer.Option(False, "-d", "--debug"),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
    config_path: str = typer.Option(None, "--config"),
    file: str = typer.Option(None, "--file", help="Open project file")
):
    """Launch Railing Infill Generator"""
    
    # Setup logging based on flags
    setup_logging(debug, verbose)
    
    # Create Qt application
    qt_app = QApplication(sys.argv)
    
    # Create main window with config
    window = MainWindow(config_path=config_path)
    
    # Load file if specified
    if file:
        window.load_project(file)
    
    window.show()
    sys.exit(qt_app.exec())

if __name__ == "__main__":
    app()
```

**Benefits:**
- Clean CLI interface: `railing-generator --debug --file project.rig.zip`
- Automatic help generation: `railing-generator --help`
- Type-safe argument parsing
- Easy to add new CLI options

**Common Qt + Typer patterns:**
- `--debug` flag for debug logging
- `--verbose` flag for console output
- `--file <path>` to open file on startup
- `--config <path>` for custom config location
- `--version` to show version info

**Verdict: Keep Typer** - Standard pattern for Qt CLI applications

### mypy (Type Checking)

**Compatibility: Excellent ✓**

**Why it works well:**
- mypy is a static analysis tool (no runtime impact)
- PySide6 has excellent type stubs (PySide6-stubs)
- Qt's Signal/Slot system is fully typed
- Catches Qt-specific errors at development time

**Type checking benefits with PySide6:**

1. **Signal/Slot type safety:**
```python
from PySide6.QtCore import Signal, Slot, QObject

class Generator(QObject):
    # Typed signals - mypy validates these!
    progress_updated = Signal(dict)  # progress_data (generator-specific)
    
    @Slot(dict)  # mypy checks slot signature matches
    def on_progress(self, progress_data: dict):
        # progress_data may contain: iteration, fitness, percentage, etc.
        # Content varies by generator type
        pass
```

2. **Widget type checking:**
```python
from PySide6.QtWidgets import QMainWindow, QWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.central: QWidget = QWidget()  # mypy knows this is QWidget
        self.setCentralWidget(self.central)  # mypy validates this call
```

3. **Catches common Qt errors:**
```python
# mypy catches this error:
widget.clicked.connect(self.wrong_signature)  # Error: incompatible types

# mypy validates this:
widget.clicked.connect(self.correct_signature)  # OK
```

**Configuration for PySide6:**
```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true

# PySide6 specific
plugins = []  # No special plugins needed
ignore_missing_imports = false  # PySide6 has stubs

[[tool.mypy.overrides]]
module = "PySide6.*"
ignore_missing_imports = false  # Use PySide6 type stubs
```

**Install type stubs:**
```bash
uv pip install PySide6-stubs
```

**Benefits:**
- Catch Signal/Slot signature mismatches
- Validate widget method calls
- Ensure proper QObject inheritance
- Type-safe configuration access
- Better IDE autocomplete

**Verdict: Keep mypy** - Essential for type-safe Qt development

### Summary: All Technologies Integrate Well

| Technology | Compatibility | Purpose | Integration |
|------------|---------------|---------|-------------|
| **Rich** | ✓ Excellent | Console logging | Parallel to GUI, no conflicts |
| **Typer** | ✓ Excellent | CLI parsing | Pre-GUI, standard Qt pattern |
| **mypy** | ✓ Excellent | Type checking | Static analysis, PySide6 stubs available |
| **Hydra** | ✓ Good | Config defaults | Hybrid with QSettings |
| **PySide6** | ✓ Native | GUI framework | Core framework |

### Recommended Tech Stack

**Final stack for the application:**

```toml
[project]
dependencies = [
    "PySide6>=6.6.0",           # GUI framework
    "PySide6-stubs",            # Type stubs for mypy
    "hydra-core>=1.3.0",        # Configuration defaults
    "omegaconf>=2.3.0",         # Config objects
    "rich>=13.0.0",             # Console logging
    "typer>=0.9.0",             # CLI parsing
    "numpy>=1.24.0",            # Geometry calculations
    "ezdxf>=1.1.0",             # DXF export
]

[project.optional-dependencies]
dev = [
    "mypy>=1.0.0",              # Type checking
    "ruff>=0.1.0",              # Linting/formatting
    "pytest>=7.0.0",            # Testing
    "pytest-qt>=4.0.0",         # Qt testing
    "pytest-cov",               # Coverage
]
```

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

## Appendix: Code Examples

### Shape Interface Example

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Shape(ABC):
    """Abstract base class for all railing frame shapes"""
    
    @abstractmethod
    def get_boundary(self) -> Polygon:
        """Returns the boundary polygon of the shape"""
        pass
    
    @abstractmethod
    def get_frame_lines(self) -> List[Line]:
        """Returns the individual frame lines"""
        pass
    
    @abstractmethod
    def validate_parameters(self, params: ShapeParameters) -> bool:
        """Validates shape parameters"""
        pass
    

    
    @abstractmethod
    def calculate_bom(self, weight_per_meter_kg_m: float) -> List[Dict[str, Any]]:
        """Calculates bill of materials for frame"""
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
infill_weight_per_meter_kg_m: 0.5
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
