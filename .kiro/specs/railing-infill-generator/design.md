# Design Document

## Overview

The Railing Infill Generator is a desktop application that generates rod arrangements for railing frames. Users define a railing frame shape (staircase or rectangular), configure generation parameters, and the application generates infill patterns using various generation algorithms. The design emphasizes extensibility, allowing new shapes and generation algorithms to be added without modifying existing code.

## Naming Convention

This section maps requirements terminology (natural English) to implementation class names (Python code).

### Requirements → Implementation Mapping

| Requirements Term | Implementation Class | Purpose |
|-------------------|---------------------|---------|
| Shape Type | `RailingShape` (ABC) | Abstract base class for shape configurations |
| Staircase Shape | `StaircaseRailingShape` | Concrete shape for stairs |
| Rectangular Shape | `RectangularRailingShape` | Concrete shape for rectangles |
| Railing Frame | `RailingFrame` | Immutable container for frame rods + boundary |
| Railing Infill | `RailingInfill` | Immutable container for infill rods |
| Rod | `Rod` | Physical bar element |

### Class Naming Pattern

- **Base classes**: `RailingXxx` (e.g., `RailingShape`, `RailingFrame`, `RailingInfill`)
- **Concrete shapes**: `XxxRailingShape` (e.g., `StaircaseRailingShape`, `RectangularRailingShape`)
- **Parameters**: `XxxRailingShapeParameters` (Pydantic models)
- **Defaults**: `XxxRailingShapeDefaults` (dataclasses for Hydra)

### Key Methods

- `RailingShape.generate_frame() -> RailingFrame` - Generate frame from configuration
- `Generator.generate(frame, params) -> RailingInfill` - Generate infill within frame
- `ViewportWidget.set_railing_frame(frame)` - Display frame
- `ViewportWidget.set_railing_infill(infill)` - Display infill

### Rationale

- **Railing prefix**: Avoids naming conflicts, makes domain clear
- **Staircase vs Stair**: More specific (staircase = multiple steps, stair = single step)
- **Frame/Infill separation**: Clear distinction between boundary and interior
- **Immutable containers**: Frame and Infill are data, not configuration

### Key Design Goals

1. **Extensibility**: Support adding new shape types and generator algorithms through plugin architecture
2. **Quality**: Generate aesthetically pleasing arrangements with uniform hole distribution
3. **Performance**: Complete generation within 60 seconds for typical cases
4. **Usability**: Provide real-time visual feedback during generation
5. **Maintainability**: Clear separation of concerns with well-defined interfaces

## Technical Standards

This application follows the Python development standards defined in `.kiro/steering/python-standards.md`, including:
- Pydantic for data models and validation
- Shapely for geometry operations
- PySide6 for GUI with Signal/Slot pattern
- Hydra for configuration management
- Layered architecture (domain, application, presentation, infrastructure)

See the steering document for general patterns. Feature-specific implementations are detailed below.

## Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                        │
│  • Main Window, Viewport, Parameter Panels, BOM Tables      │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                         │
│  • Application Controller, State Management, Event Handlers │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                            │
│  • Shapes, Generators, Rod, Quality Evaluator               │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                       │
│  • Configuration, File I/O, Export, Logging                 │
└─────────────────────────────────────────────────────────────┘
```

### Design Patterns

- **Strategy Pattern**: Shapes and generators (runtime algorithm selection)
- **Factory Pattern**: Create instances based on type strings
- **Observer Pattern**: PySide6 Signal/Slot for event handling
- **Repository Pattern**: Configuration and data access abstraction

## Core Concepts

### 1. Shape System

The shape system consists of configuration classes (`RailingShape` subclasses) that generate immutable frame data (`RailingFrame`).

**Architecture:**
```
RailingShape (configuration) → generate_frame() → RailingFrame (immutable data)
                                                        ↓
                                                   Viewport renders
```

**Shape Types:**
- **StaircaseRailingShape**: Two vertical posts + angled handrail + stepped bottom
- **RectangularRailingShape**: Simple rectangular frame
- **Future**: Curved, custom polygon shapes

**RailingShape Interface (ABC):**
```python
class RailingShape(ABC):
    @abstractmethod
    def generate_frame(self) -> RailingFrame:
        """Generate immutable frame containing rods and boundary."""
        ...
```

**RailingFrame (Immutable Container):**
```python
class RailingFrame(BaseModel):
    rods: list[Rod]              # Frame rods (layer 0)
    boundary: Polygon            # Frame boundary polygon
    # Computed properties:
    total_length_cm: float
    total_weight_kg: float
    rod_count: int
    
    model_config = {"frozen": True}  # Immutable
```

**Parameters** (Pydantic models for UI validation):
- `StaircaseRailingShapeParameters`: post_length_cm, stair_width_cm, stair_height_cm, num_steps, frame_weight_per_meter_kg_m
- `RectangularRailingShapeParameters`: width_cm, height_cm, frame_weight_per_meter_kg_m
- Initialized with defaults from Hydra config (dataclass)
- Pydantic validation errors displayed in UI

### 2. Generator System

Generators create infill rod arrangements within a frame boundary, producing immutable `RailingInfill` containers.

**Architecture:**
```
Generator + RailingFrame + Parameters → generate() → RailingInfill (immutable data)
```

**Generator Types:**
- **Random Generator**: Iterative random placement with fitness evaluation
- **Future**: Pattern-based, ML-based, user-guided generators

**Random Generator Process:**
1. Select random anchor points along frame (Shapely LineString.interpolate)
2. Generate rods with random angles (deviation from vertical)
3. Ensure no crossings within same layer (Shapely LineString.intersects)
4. Evaluate fitness score using Quality Evaluator
5. Keep best arrangement, repeat until acceptable or limit reached

**Generator Interface:**
```python
class Generator(QObject, ABC):
    progress_updated = Signal(dict)
    best_result_updated = Signal(object)  # RailingInfill
    generation_completed = Signal(object)  # RailingInfill
    generation_failed = Signal(str)
    
    @abstractmethod
    def generate(self, frame: RailingFrame, params: BaseModel) -> RailingInfill:
        """Generate infill within the given frame."""
        ...
```

**RailingInfill (Immutable Container):**
```python
class RailingInfill(BaseModel):
    rods: list[Rod]                    # Infill rods (layer ≥ 1)
    fitness_score: float | None        # Optional fitness score
    iteration_count: int | None        # Optional iteration count
    duration_sec: float | None         # Optional generation duration
    
    model_config = {"frozen": True}    # Immutable
```

**Parameters** (Pydantic models for UI validation):
- `RandomGeneratorParameters`: num_rods, max_rod_length_cm, max_angle_deviation_deg, num_layers, min_anchor_distance_cm, max_iterations, max_duration_sec
- Initialized with defaults from Hydra config (dataclass)
- Pydantic validation errors displayed in UI

### 3. Quality Evaluator

Scores infill arrangements using weighted criteria (used by Random Generator).

**Evaluation Criteria:**
1. **Hole Uniformity**: Similar hole areas
2. **Incircle Uniformity**: Uniform incircle radii
3. **Angle Distribution**: Avoid too vertical or too angled rods
4. **Anchor Spacing**: Evenly distributed anchors
   - Separate weights for horizontal (top/bottom) vs vertical (posts) elements

**Shapely Operations:**
- `polygonize()` - Identify holes from rod arrangement
- `Polygon.area` - Calculate hole areas
- `Point.distance()` - Measure anchor spacing

### 4. Multi-Layer System

Rods organized into layers (rules vary by generator).

**Random Generator:**
- Rods within same layer cannot cross
- Rods in different layers can cross
- Default: 2 layers, each rendered in different color

## Data Models

### Rod (Pydantic BaseModel)

Unified representation for frame and infill rods.

**Fields:**
- `geometry: LineString` - Shapely geometry
- `start_cut_angle_deg: float` - Constrained -90° to 90°
- `end_cut_angle_deg: float` - Constrained -90° to 90°
- `weight_kg_m: float` - Must be positive
- `layer: int` - 0 for frame, ≥1 for infill

**Computed Fields:**
- `length_cm`, `weight_kg`, `start_point`, `end_point`

**Methods:**
- `model_dump()`, `model_dump_json()` - Serialization
- `to_bom_entry(rod_id)` - Generate BOM table row

### InfillResult (Pydantic BaseModel)

**Fields:**
- `rods: list[Rod]` - List of Rod objects with layer assignments
- `fitness_score: float | None` - Optional fitness score (for generators using evaluator)
- `iteration_count: int | None` - Optional iteration count (for iterative generators)
- `duration_sec: float | None` - Optional generation duration

**Features:**
- Immutable once created (consider using `frozen=True` if needed)
- Automatic serialization via `model_dump()` and `model_dump_json()`
- Rods automatically serialized (Pydantic handles nested models)
- BOM entries generated via `Rod.to_bom_entry()` for each rod

### QualityEvaluator (Used by Random Generator)

**Purpose:** Scores infill arrangements using multiple weighted criteria.

**Methods:**
- `evaluate(arrangement, shape, params)` → float (fitness score, higher = better)
- `is_acceptable(arrangement, shape, params)` → bool (checks if arrangement meets minimum criteria)

**Evaluation Process:**
1. Identify all holes by combining frame and infill rod geometries into a line network, then use Shapely `polygonize()` to extract enclosed polygons (holes)
2. Calculate hole areas using `Polygon.area`
3. Calculate incircle radii (approximate using `Polygon.minimum_rotated_rectangle` or inscribed circle algorithms)
4. Analyze rod angles and anchor spacing
5. Compute individual criterion scores (0-1, where 1 = perfect)
6. Combine using configured weights
7. Reject if any hole exceeds max area

**How Hole Identification Works (Complex Case with Crossing Rods):**

`polygonize()` has a critical limitation: it only works when lines meet at **endpoints**, not when they cross in the middle. Since infill rods can cross each other (different layers), we need preprocessing to create a "noded" network.

**The Problem:**
- When two lines cross, there may not be a node (vertex) at the intersection point
- This is called a "non-noded intersection"
- `polygonize()` fails to recognize these crossings and produces incorrect or missing polygons

**The Solution - Use `shapely.node()`:**

Shapely 2.0+ provides the `node()` function which adds nodes at all intersection points:

```python
import shapely
from shapely.ops import polygonize

def find_holes(frame_rods, infill_rods):
    # Combine all rod geometries
    all_rods = [rod.geometry for rod in (frame_rods + infill_rods)]
    
    # Combine to a single GeometryCollection
    collection = shapely.GeometryCollection(all_rods)
    
    # Add nodes at all intersection points (creates "noded" network)
    noded = shapely.node(collection)
    
    # Now polygonize can correctly identify all enclosed polygons
    holes = list(polygonize(noded.geoms))
    
    return holes
```

**How `shapely.node()` works:**
1. Takes a GeometryCollection of linestrings
2. Finds all intersection points where lines cross
3. Splits each line at intersection points, adding explicit nodes
4. Returns a new GeometryCollection with the noded (split) lines
5. The result can be properly processed by `polygonize()`

**Example:**
```
Before noding:              After noding:
Rod A: ────────            Rod A: ───┼───  (split into 2 segments)
Rod B:    │                Rod B:    │     (split into 2 segments)
          │                          │
```

**Requirements:**
- Shapely 2.0 or newer (for `shapely.node()` function)
- All infill rods must be anchored to the frame to form closed polygons

**Reference:** This approach is used by QGIS for polygonization and is documented at:
https://martinfleischmann.net/fixing-missing-geometries-in-a-polygonized-network/

**Criteria Details:**
- **Hole Uniformity** (weight: 0.3): Prefer similar hole areas across all holes
- **Incircle Uniformity** (weight: 0.2): Prefer uniform incircle radii
- **Angle Distribution** (weight: 0.2): Penalize rods too vertical or too angled
- **Anchor Spacing Horizontal** (weight: 0.15): Evenly distributed anchors on top/bottom frame elements
- **Anchor Spacing Vertical** (weight: 0.15): Evenly distributed anchors on post frame elements

**Configuration:**
- Criteria weights loaded from `conf/evaluator/criteria.yaml`
- Max hole area threshold (cm²) for rejection
- Separate weights for horizontal vs vertical anchor spacing

## Application Layer

### Application Controller

Orchestrates application workflows.

**Key Methods:**
- `create_new_project()` - Reset to defaults
- `update_shape(type, params)` - Create new shape
- `generate_infill(type, params)` - Start generation in background thread
- `cancel_generation()` - Cancel ongoing generation
- `save_project(path)` - Save to .rig.zip
- `load_project(path)` - Load from .rig.zip
- `export_dxf(path)` - Export to DXF

### Project State

**Components:**
- Shape type and parameters
- Shape instance
- Generator type and parameters
- Infill result (if generated)
- File path and modified flag

## Presentation Layer

### Main Window Layout

**Window Title Format:**
- `{filename}* - Railing Infill Generator` (asterisk if unsaved changes)
- Example: `project.rig.zip* - Railing Infill Generator`
- Example: `Untitled* - Railing Infill Generator`

```
┌─────────────────────────────────────────────────────────────┐
│  Title: project.rig.zip* - Railing Infill Generator         │
│  Menu Bar: File | View | Help                               │
├──────────────┬──────────────────────────────────────────────┤
│  Parameter   │      Viewport (zoom, pan, render)            │
│  Panel       │                                              │
│  - Shape     ├──────────────────────────────────────────────┤
│  - Generator │  BOM Table (2 tabs: Frame | Infill)         │
│  - Buttons   │  - ID, Length, Start Angle, End Angle, Weight│
├──────────────┴──────────────────────────────────────────────┤
│  Status Bar: Ready | Rods: 50                               │
└─────────────────────────────────────────────────────────────┘
```

**Status Bar:**
- Left: Operation status ("Ready", "Generating...", "Saved")
- Right: Quick stats (rod count, quality metrics if available)

### Key UI Components

#### Viewport (QGraphicsView/QGraphicsScene)
- Vector-based rendering using QGraphicsScene
- Zoom with mouse wheel (centered on cursor position)
- Pan with mouse drag
- Render frame in distinct color
- Render infill with layer-specific colors
- Optional rod enumeration (circles for infill, squares for frame, dashed anchor lines)
- Part highlighting on BOM selection
- Performance optimizations:
  - `setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)` for efficient updates
  - `setItemIndexMethod(QGraphicsScene.NoIndex)` for static scenes
  - `setCacheMode(QGraphicsItem.DeviceCoordinateCache)` for cached rendering
  - Signal throttling (max every 100ms for progress updates)

#### Parameter Panel (QFormLayout with Dynamic Widgets)
- Dynamic form using QFormLayout for automatic label alignment
- QComboBox for shape/generator type selection
- QDoubleSpinBox/QSpinBox for numeric inputs with validation
- Unit suffixes displayed (cm, kg, °)
- Show/hide parameters based on selected type
- Real-time validation with inline error display
- "Update Shape" button (short operation, disables UI during execution)
- "Generate Infill" button (long operation, opens progress dialog)

#### BOM Table (QTableWidget with QTabWidget)
- Two tabs: Frame Parts, Infill Parts
- Columns: ID, Length (cm), Start Angle (°), End Angle (°), Weight (kg)
- Sortable columns
- Per-tab totals: Sum Length, Sum Weight
- Combined totals: Total Length, Total Weight
- Row selection triggers viewport highlighting
- Export to CSV via save function

#### Progress Dialog (QDialog)
- Modal dialog blocking main window input
- QProgressBar or text-based progress indicator
- Real-time metrics display (iteration, fitness, elapsed time)
- QTextEdit for progress logs
- Cancel button (sets cancellation flag)
- Updates viewport with best result in real-time
- Closes on completion or cancellation

## Infrastructure Layer

### Configuration Structure

```
conf/
├── config.yaml              # Main config
├── shapes/
│   ├── stair.yaml          # Stair defaults
│   └── rectangular.yaml    # Rectangular defaults
├── generators/
│   └── random.yaml         # Random generator defaults
├── evaluator/
│   └── criteria.yaml       # Quality criteria weights
├── ui/
│   └── settings.yaml       # UI settings (colors, PNG resolution)
└── logging/
    └── config.yaml         # Logger hierarchy and levels
```

**Hybrid Configuration Approach:**

1. **Hydra for Application Defaults** (version controlled)
   - Shape default parameters
   - Generator default parameters
   - Quality evaluator criteria
   - UI settings (colors, resolution)
   - Logging configuration
   - Stored in `conf/` directory

2. **QSettings for User Preferences** (not version controlled)
   - Window geometry and state
   - Recent files list
   - Last used shape/generator types
   - User-modified parameter values
   - UI preferences (panel sizes, etc.)
   - Stored in platform-specific location

**Configuration Loading:**
- Hydra loads YAML → Dataclass (defaults)
- Dataclass → Pydantic models for UI validation
- QSettings overrides with user preferences
- Same Pydantic models used for UI parameter panels

**Implementation Pattern:**
```python
class AppConfig:
    def __init__(self):
        # Load defaults from Hydra
        self.defaults = self._load_hydra_config()
        
        # Load user preferences from QSettings
        self.settings = QSettings("RailingGenerator", "RailingApp")
    
    def get_parameter(self, key: str, default=None):
        """Get parameter, preferring user setting over default"""
        if self.settings.contains(key):
            return self.settings.value(key)
        return self.defaults.get(key, default)
    
    def set_user_preference(self, key: str, value):
        """Save user preference"""
        self.settings.setValue(key, value)
```

### Geometry Operations (Feature-Specific)

This application uses Shapely extensively for geometric calculations:

**Common Operations:**
- `LineString.interpolate(distance)` - Get point at distance along frame for anchor points
- `LineString.intersects(other)` - Check if rods cross (same layer constraint)
- `Point.distance(other)` - Measure anchor spacing for quality evaluation
- `Polygon.area` - Calculate hole areas for quality criteria
- `polygonize(lines)` - Extract enclosed polygons (holes) from a network of lines

**Example Usage:**
```python
from shapely.geometry import LineString, Point
from shapely.ops import polygonize

# Get anchor point along frame
frame_line = LineString([(0, 0), (100, 0)])
anchor = frame_line.interpolate(50.0)  # Point at 50cm along frame

# Check if rods intersect (same layer)
rod1 = LineString([(10, 0), (10, 100)])
rod2 = LineString([(20, 0), (20, 100)])
crosses = rod1.intersects(rod2)  # False

# Find holes for quality evaluation
import shapely
from shapely.ops import polygonize

# Combine all rod geometries (frame + infill) into one collection
all_rod_geometries = [rod.geometry for rod in (frame_rods + infill_rods)]

# IMPORTANT: Since rods can cross each other (different layers), we need to
# create a "noded" network where lines are split at intersection points
collection = shapely.GeometryCollection(all_rod_geometries)

# shapely.node() adds nodes at all intersection points, splitting lines
noded = shapely.node(collection)

# Now polygonize() can correctly identify all enclosed polygons (holes)
holes = list(polygonize(noded.geoms))

# Calculate areas of all holes
hole_areas = [hole.area for hole in holes]

# Example: Rectangular frame + 3 vertical rods + 2 diagonal crossing rods
# After noding splits at crossings, polygonize() returns all enclosed polygons
```

**Important Notes on Hole Identification:**
- `polygonize()` requires lines to meet at endpoints, not cross in the middle
- Since rods can cross (different layers), preprocessing with `shapely.node()` is required
- `shapely.node()` creates a "noded" network by splitting lines at intersection points
- Requires Shapely 2.0 or newer
- The frame boundary must be a closed loop (connected lines)
- Infill rods must be anchored to the frame to form closed holes
- This is a complex geometric operation that may require testing and refinement
- Consider edge cases: very small holes, nearly-parallel rods, numerical precision issues

### File Management

**Save Format (.rig.zip):**
- `parameters.json` - All shape/generator parameters
- `infill_geometry.json` - Rod coordinates and layers
- `preview.png` - Viewport screenshot
- `frame_bom.csv` - Frame parts table
- `infill_bom.csv` - Infill parts table

**DXF Export:**
- Separate layers: "FRAME" and "INFILL"
- Each rod as LINE entity
- Dimensions in cm

## Data Flow

### Shape Update Flow

```
User selects shape type → Parameter panel updates → User enters parameters →
User clicks "Update Shape" → Validate parameters (dataclass __post_init__) →
Create shape instance → Viewport renders frame → BOM table updates
```

### Infill Generation Flow

```
User configures generator → User clicks "Generate Infill" →
Validate parameters (dataclass __post_init__) → Progress dialog opens →
Generator runs in QThread:
  - Execute generation algorithm
  - Emit progress_updated signal → Update progress dialog
  - Emit best_result_updated signal → Update viewport
  - Complete when done
→ Progress dialog closes → Viewport shows final result → BOM table updates
```

### Save/Load Flow

```
User clicks Save/Save As → File dialog → Create ZIP archive:
  - Serialize parameters (dataclasses.asdict + json.dumps)
  - Serialize infill geometry (Pydantic model_dump_json for Rod/InfillResult)
  - Render viewport to PNG
  - Export BOM tables to CSV
→ Mark project as saved → Update window title
```

## Error Handling

### Error Categories

**Validation Errors:**
- Invalid parameters (negative dimensions, out of range values)
- Pydantic raises ValidationError with field-specific messages
- Display: Red highlighting in parameter panel + tooltip with error message
- Recovery: User corrects input, validation happens in real-time

**Generation Errors:**
- No valid arrangement found within iteration/time limits
- Display: Error message in progress dialog with details
- Recovery: User adjusts parameters (increase limits, relax constraints) and retries

**File I/O Errors:**
- Cannot read/write files (permissions, disk space, corrupted files)
- Invalid ZIP structure or JSON schema on load
- Display: Modal error dialog with specific error details
- Recovery: Choose different location, check permissions, or verify file integrity

**Unexpected Errors:**
- Bugs, crashes, unhandled exceptions
- Display: Generic error dialog with stack trace
- Recovery: Log details to file, suggest restart, provide bug report option

### Error Display Strategy

- **Validation**: Inline feedback (immediate, non-blocking)
- **Operations**: Progress dialog or modal (contextual, blocking during operation)
- **Critical**: Modal dialog with details (blocking, requires acknowledgment)
- **All errors**: Logged with stack traces to log file for debugging


## Performance Considerations

### Generation Performance

**Target:** < 60 seconds for 1000 iterations with typical parameters


### UI Responsiveness

**Threading Strategy:**
- Generator runs in separate QThread (moveToThread pattern)
- Generator emits signals for progress updates
- UI connects to signals and updates accordingly
- Signals are thread-safe (Qt handles cross-thread communication)
- Cancel via atomic flag checked by generator

**Signal Throttling:**
- Emit progress signals max every 100ms
- Use QTimer for throttling if needed
- Batch viewport updates to reduce redraws

### Memory Management

**Considerations:**
- Only store best arrangement during generation (discard failed attempts)
- Clear viewport scene when loading new project
- Use QGraphicsScene.clear() to remove all items
- Lazy rendering: only render visible items when possible

### QGraphicsView Optimizations

**Rendering Performance:**
- `setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)` - Update only changed regions
- `setItemIndexMethod(QGraphicsScene.NoIndex)` - For static scenes (no item queries)
- `setCacheMode(QGraphicsItem.DeviceCoordinateCache)` - Cache rendered items
- `setRenderHint(QPainter.Antialiasing, False)` - Faster rendering for many items (trade-off with quality)

**Scene Management:**
- Use `itemsBoundingRect()` for view fitting
- Defer enumeration rendering until toggled on
- Group related items for batch operations

## Testing Strategy

### Unit Tests

**Domain Layer:**
- Rod class: geometry operations, serialization (`model_dump`, `model_dump_json`), BOM generation, computed fields
- Shape implementations: boundary calculation, frame rod generation, parameter validation, Shapely geometry correctness
- Generator logic: arrangement generation, layer organization, constraint enforcement, Shapely operations
- Quality evaluator: fitness calculations, individual criterion scores, hole identification using `polygonize()`

**Infrastructure Layer:**
- File I/O: save/load operations, ZIP structure validation, JSON schema validation
- DXF export: layer organization, entity creation, coordinate accuracy
- Configuration loading: Hydra config parsing, Pydantic validation, default value loading

### Integration Tests

**Cross-Layer:**
- Shape + Generator integration: valid arrangements for different shapes
- Generator + Evaluator integration: fitness scoring, arrangement acceptance
- Application controller workflows: complete user workflows (create, generate, save)
- End-to-end save/load cycle: data integrity, round-trip accuracy

### UI Tests (pytest-qt)

**Presentation Layer:**
- Parameter panel: updates on type selection, validation display, dynamic widget visibility
- Viewport rendering: accurate geometry display, zoom/pan functionality, highlighting
- BOM table: correct calculations, totals accuracy, selection behavior
- Progress dialog: signal handling, cancellation, real-time updates

**Testing with pytest-qt:**
```python
def test_generation_progress(qtbot):
    generator = RandomGenerator(evaluator)
    
    # Wait for signal with timeout
    with qtbot.waitSignal(generator.progress_updated, timeout=1000):
        generator.generate(shape, params)
    
    assert generator.best_fitness > 0

def test_viewport_rendering(qtbot, main_window):
    # Simulate user interaction
    qtbot.mouseClick(main_window.update_shape_button, Qt.LeftButton)
    
    # Wait for rendering
    qtbot.wait(100)
    
    # Verify viewport content
    assert main_window.viewport.scene().items()
```

### Test Data

- Predefined shape configurations (valid and invalid)
- Known-good infill arrangements for regression testing
- Edge cases: minimum/maximum parameters, boundary conditions
- Invalid inputs for validation testing
- Performance benchmarks for generation speed

## Dependencies

**Runtime Dependencies:**
- PySide6 (UI framework)
- PySide6-stubs (type stubs for mypy)
- pydantic (parameter validation and data models)
- shapely >= 2.0 (geometry operations, requires 2.0+ for `shapely.node()`)
- hydra-core (configuration management)
- omegaconf (config objects)
- rich (logging with color)
- typer (CLI interface)
- numpy (advanced numerical operations when Shapely is insufficient)
- ezdxf (DXF export)

**Development Dependencies:**
- mypy (type checking)
- ruff (formatting and linting)
- pytest (testing framework)
- pytest-qt (Qt/PySide6 testing)
- pytest-cov (coverage reporting)

## Deployment

### Package Structure

```
railing-generator/
├── src/
│   └── railing_generator/
│       ├── __main__.py          # Entry point
│       ├── app.py               # Application setup
│       ├── domain/              # Business logic
│       ├── application/         # Orchestration
│       ├── presentation/        # UI layer
│       ├── infrastructure/      # External services
│       └── resources/           # Optional: icons, images
│           ├── icons/
│           └── resources.qrc
├── conf/                        # Hydra configs
├── tests/                       # Test files
├── pyproject.toml              # Project metadata
└── README.md                   # Documentation
```

### Entry Point

**Command-line interface:**
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

**CLI Options:**
- `-d, --debug`: Enable debug logging
- `-v, --verbose`: Log to stdout in addition to file
- `--config-path`: Custom config directory (override default `conf/`)

### Deployment Options

1. **pyside6-deploy** (recommended for PySide6 apps):
   - Creates standalone executables
   - Handles Qt dependencies automatically
   - Generates `pysidedeploy.spec` config file

2. **PyInstaller/Nuitka**:
   - More control over packaging
   - Requires manual Qt plugin configuration
   - Good for advanced customization

3. **Python Package** (pip installable):
   - Distribute via PyPI or private repository
   - Users install with `pip install railing-generator`
   - Requires Python environment on target system

### Development Workflow

```bash
# Development with debug logging and console output
uv run railing-generator --debug --verbose

# Type checking (validates Qt types and Signal/Slot signatures)
uv run mypy src/

# Testing (includes pytest-qt for GUI testing)
uv run pytest

# Production (clean GUI without console output)
railing-generator
```

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

## Code Examples

### Shape Interface (Feature-Specific Implementation)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from pydantic import BaseModel, Field, field_validator
from shapely.geometry import Polygon, LineString

# Configuration defaults (dataclass for Hydra)
@dataclass
class StaircaseRailingShapeDefaults:
    """Default values loaded from Hydra YAML config (conf/shapes/staircase.yaml)"""
    post_length_cm: float = 150.0
    stair_width_cm: float = 280.0
    stair_height_cm: float = 280.0
    num_steps: int = 10
    frame_weight_per_meter_kg_m: float = 0.5

@dataclass
class RectangularRailingShapeDefaults:
    """Default values loaded from Hydra YAML config (conf/shapes/rectangular.yaml)"""
    width_cm: float = 200.0
    height_cm: float = 100.0
    frame_weight_per_meter_kg_m: float = 0.5

# Parameter models (Pydantic for UI validation)
class StaircaseRailingShapeParameters(BaseModel):
    """Runtime parameters with Pydantic validation for UI"""
    post_length_cm: float = Field(gt=0, description="Post length in cm")
    stair_width_cm: float = Field(gt=0, description="Stair width (horizontal distance) in cm")
    stair_height_cm: float = Field(gt=0, description="Stair height (vertical distance) in cm")
    num_steps: int = Field(ge=1, le=50, description="Number of steps")
    frame_weight_per_meter_kg_m: float = Field(gt=0, description="Frame weight per meter")
    
    @field_validator('post_length_cm', 'stair_width_cm', 'stair_height_cm')
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Must be positive')
        return v
    
    @classmethod
    def from_defaults(cls, defaults: StaircaseRailingShapeDefaults) -> "StaircaseRailingShapeParameters":
        """Create parameters from config defaults"""
        return cls(
            post_length_cm=defaults.post_length_cm,
            stair_width_cm=defaults.stair_width_cm,
            stair_height_cm=defaults.stair_height_cm,
            num_steps=defaults.num_steps,
            frame_weight_per_meter_kg_m=defaults.frame_weight_per_meter_kg_m
        )

class RectangularRailingShapeParameters(BaseModel):
    """Runtime parameters with Pydantic validation for UI"""
    width_cm: float = Field(gt=0, description="Width in cm")
    height_cm: float = Field(gt=0, description="Height in cm")
    frame_weight_per_meter_kg_m: float = Field(gt=0, description="Frame weight per meter")
    
    @classmethod
    def from_defaults(cls, defaults: RectangularRailingShapeDefaults) -> "RectangularRailingShapeParameters":
        """Create parameters from config defaults"""
        return cls(
            width_cm=defaults.width_cm,
            height_cm=defaults.height_cm,
            frame_weight_per_meter_kg_m=defaults.frame_weight_per_meter_kg_m
        )

class RailingShape(ABC):
    """Abstract base class for all railing frame shape configurations"""
    
    def __init__(self, params: BaseModel):  # Accepts Pydantic model
        """
        Initialize shape configuration with validated parameters.
        Parameters are Pydantic models validated before passing here.
        """
        self.params = params
    
    @abstractmethod
    def generate_frame(self) -> RailingFrame:
        """Generate immutable RailingFrame containing rods and boundary"""
        pass

# Usage in UI:
# 1. Load defaults from Hydra config (dataclass)
# 2. Create Pydantic parameter model from defaults
# 3. User modifies in UI, Pydantic validates
# 4. Pass validated Pydantic model to RailingShape constructor
# 5. Call generate_frame() to get immutable RailingFrame
```

### Generator Interface (Feature-Specific Implementation)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pydantic import BaseModel, Field
from PySide6.QtCore import QObject, Signal

# Configuration defaults (dataclass for Hydra)
@dataclass
class RandomGeneratorDefaults:
    """Default values loaded from Hydra YAML config (conf/generators/random.yaml)"""
    num_rods: int = 50
    max_rod_length_cm: float = 200.0
    max_angle_deviation_deg: float = 30.0
    num_layers: int = 2
    min_anchor_distance_cm: float = 10.0
    max_iterations: int = 1000
    max_duration_sec: float = 60.0
    infill_weight_per_meter_kg_m: float = 0.3

# Parameter models (Pydantic for UI validation)
class RandomGeneratorParameters(BaseModel):
    """Runtime parameters with Pydantic validation for UI"""
    num_rods: int = Field(ge=1, le=200, description="Number of infill rods")
    max_rod_length_cm: float = Field(gt=0, description="Maximum rod length")
    max_angle_deviation_deg: float = Field(ge=0, le=45, description="Max angle from vertical")
    num_layers: int = Field(ge=1, le=5, description="Number of layers")
    min_anchor_distance_cm: float = Field(gt=0, description="Min distance between anchors")
    max_iterations: int = Field(ge=1, description="Maximum iterations")
    max_duration_sec: float = Field(gt=0, description="Maximum duration in seconds")
    infill_weight_per_meter_kg_m: float = Field(gt=0, description="Infill rod weight per meter")
    
    @classmethod
    def from_defaults(cls, defaults: RandomGeneratorDefaults) -> "RandomGeneratorParameters":
        """Create parameters from config defaults"""
        return cls(
            num_rods=defaults.num_rods,
            max_rod_length_cm=defaults.max_rod_length_cm,
            max_angle_deviation_deg=defaults.max_angle_deviation_deg,
            num_layers=defaults.num_layers,
            min_anchor_distance_cm=defaults.min_anchor_distance_cm,
            max_iterations=defaults.max_iterations,
            max_duration_sec=defaults.max_duration_sec,
            infill_weight_per_meter_kg_m=defaults.infill_weight_per_meter_kg_m
        )

class Generator(QObject, ABC):
    """Abstract base class for all infill generators"""
    progress_updated = Signal(dict)  # {"iteration": int, "best_fitness": float, "elapsed_sec": float}
    best_result_updated = Signal(object)  # RailingInfill
    generation_completed = Signal(object)  # RailingInfill
    generation_failed = Signal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self._cancelled = False
    
    @abstractmethod
    def generate(self, frame: RailingFrame, params: BaseModel) -> RailingInfill:
        """
        Generate infill arrangement within the given frame.
        Emits signals during generation for progress updates.
        """
        pass
    
    def cancel(self):
        """Request cancellation of ongoing generation"""
        self._cancelled = True
```

### Rod Class (Feature-Specific Implementation)

```python
from pydantic import BaseModel, Field, computed_field
from shapely.geometry import LineString, Point
from typing import Dict, Any

class Rod(BaseModel):
    """
    Unified representation for frame and infill rods.
    Uses Shapely LineString for geometry operations.
    """
    geometry: LineString = Field(exclude=True)  # Excluded from serialization
    start_cut_angle_deg: float = Field(ge=-90, le=90, description="Cut angle at start point")
    end_cut_angle_deg: float = Field(ge=-90, le=90, description="Cut angle at end point")
    weight_kg_m: float = Field(gt=0, description="Weight per meter")
    layer: int = Field(ge=0, default=0, description="Layer (0=frame, >=1=infill)")
    
    model_config = {"arbitrary_types_allowed": True}  # Required for Shapely types
    
    @computed_field
    @property
    def length_cm(self) -> float:
        """Calculate rod length from geometry"""
        return self.geometry.length
    
    @computed_field
    @property
    def weight_kg(self) -> float:
        """Calculate rod weight from length and weight per meter"""
        return (self.length_cm / 100.0) * self.weight_kg_m
    
    @computed_field
    @property
    def start_point(self) -> Point:
        """Get start point of rod"""
        return Point(self.geometry.coords[0])
    
    @computed_field
    @property
    def end_point(self) -> Point:
        """Get end point of rod"""
        return Point(self.geometry.coords[-1])
    
    def to_bom_entry(self, rod_id: int) -> Dict[str, Any]:
        """Convert rod to BOM table entry"""
        return {
            "id": rod_id,
            "length_cm": round(self.length_cm, 2),
            "start_cut_angle_deg": round(self.start_cut_angle_deg, 1),
            "end_cut_angle_deg": round(self.end_cut_angle_deg, 1),
            "weight_kg": round(self.weight_kg, 3)
        }
    
    def model_dump_geometry(self) -> Dict[str, Any]:
        """Serialize including geometry as coordinate list"""
        data = self.model_dump()
        data["geometry"] = list(self.geometry.coords)
        return data
```
