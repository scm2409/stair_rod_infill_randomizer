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

- **Strategy Pattern**: Shapes, generators, and evaluators (runtime algorithm selection)
- **Factory Pattern**: Create instances based on type strings (shapes, generators, evaluators)
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
- **Random Generator (V1)**: Iterative random placement with fitness evaluation
- **Random Generator V2**: Enhanced layered directional approach with frame-aware anchor spacing and fitness evaluation
- **Future**: Pattern-based, ML-based, user-guided generators

**Evaluator Types:**
- **Quality Evaluator**: Multi-criteria fitness scoring (hole uniformity, incircle uniformity, angle distribution, anchor spacing)
- **Pass-Through Evaluator**: Returns first valid arrangement without scoring (fastest, no optimization)
- **Future**: Structural evaluator, aesthetic evaluator, cost evaluator, custom evaluators

**Random Generator V1 Process:**
1. Select random anchor points along frame (Shapely LineString.interpolate)
2. Generate rods with random angles (deviation from vertical)
3. Ensure no crossings within same layer (Shapely LineString.intersects)
4. Evaluate fitness score using selected evaluator
5. Keep best arrangement, repeat until acceptable or limit reached

**Random Generator V2 Process:**
1. Pre-generate anchor points with frame-segment-aware spacing (different densities for vertical vs horizontal frame segments)
2. Distribute anchors evenly across layers with randomization
3. Calculate main direction for each layer (evenly distributed across configured angle range)
4. For each layer: project from random anchor at target angle (main direction ± random deviation), find nearest anchor on opposite side
5. Validate constraints (length, boundary, no same-layer crossings)
6. Evaluate fitness score using selected evaluator
7. Generate multiple attempts, return best arrangement

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
- `RandomGeneratorParameters`: 
  - `num_rods`, `max_rod_length_cm`, `max_angle_deviation_deg`, `num_layers`, `min_anchor_distance_cm`
  - `max_iterations`, `max_duration_sec`: Control rod generation process (how long to try generating valid rods for ONE arrangement)
  - `max_evaluation_attempts`: How many complete arrangements to generate and evaluate (default: 10)
  - `max_evaluation_duration_sec`: Maximum time for entire evaluation loop (default: 60.0)
  - `min_acceptable_fitness`: Minimum fitness score to accept early and stop evaluation loop (default: 0.7)
- `RandomGeneratorParametersV2`: Extends base parameters with:
  - `min_anchor_distance_vertical_cm`: Spacing for vertical frame segments (e.g., posts)
  - `min_anchor_distance_other_cm`: Spacing for horizontal/sloped frame segments (e.g., handrails)
  - `main_direction_range_min_deg`, `main_direction_range_max_deg`: Range for layer main directions
  - `random_angle_deviation_deg`: Random deviation from layer main direction
- Initialized with defaults from Hydra config (dataclass)
- Pydantic validation errors displayed in UI

**Two-Level Control System:**
1. **Inner Loop** (`max_iterations`, `max_duration_sec`): Controls rod generation for a single arrangement
2. **Outer Loop** (`max_evaluation_attempts`, `max_evaluation_duration_sec`, `min_acceptable_fitness`): Controls evaluation loop (generator's responsibility)

Example: With `max_iterations=1000` and `max_evaluation_attempts=10`:
- Try up to 1000 iterations to generate each arrangement
- Generate and evaluate up to 10 complete arrangements
- Stop early if fitness ≥ `min_acceptable_fitness`
- Return the best arrangement found

### 3. Evaluator System

Evaluators are required components that score infill arrangements. Both Random Generator V1 and V2 must use an evaluator. Different evaluators provide different optimization strategies.

**Evaluator Types:**
- **Quality Evaluator**: Multi-criteria fitness scoring for optimal visual quality (default)
- **Pass-Through Evaluator**: Returns first valid arrangement without scoring (fastest, no optimization)
- **Future**: Structural evaluator, aesthetic evaluator, cost evaluator, custom evaluators

**Quality Evaluator:**

Scores infill arrangements using weighted criteria for optimal visual quality.

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

**Parameters** (Pydantic models for UI validation):
- `QualityEvaluatorParameters`: 
  - `max_hole_area_cm2`: Maximum allowed hole area (rejection threshold)
  - `hole_uniformity_weight`: Weight for hole uniformity criterion (0-1)
  - `incircle_uniformity_weight`: Weight for incircle uniformity criterion (0-1)
  - `angle_distribution_weight`: Weight for angle distribution criterion (0-1)
  - `anchor_spacing_horizontal_weight`: Weight for horizontal anchor spacing (0-1)
  - `anchor_spacing_vertical_weight`: Weight for vertical anchor spacing (0-1)
- Initialized with defaults from Hydra config (dataclass)
- Pydantic validation errors displayed in UI

**Note**: Evaluator only scores individual arrangements. The generator controls the evaluation loop using its own parameters.

**Pass-Through Evaluator:**

Returns first valid arrangement without scoring. Fastest option when quality optimization is not needed.

**Behavior:**
- `evaluate()`: Always returns 1.0 (neutral score)
- `is_acceptable()`: Always returns True (accepts first valid arrangement)
- No computational overhead for fitness calculation
- Useful for quick previews or when speed is priority

**Parameters** (Pydantic models for UI validation):
- `PassThroughEvaluatorParameters`: No parameters (empty model)
- No configuration needed

**Usage with Generators:**
- **V1 with Quality Evaluator**: 
  - Inner loop: Generates each arrangement using `max_iterations`/`max_duration_sec`
  - Outer loop: Evaluates multiple arrangements up to `max_evaluation_attempts`/`max_evaluation_duration_sec`
  - Stops when `min_acceptable_fitness` reached or limits hit
  - Returns best arrangement found
- **V1 with Pass-Through**: 
  - Generates one arrangement using `max_iterations`/`max_duration_sec`
  - Returns first valid arrangement (fast, no evaluation loop)
- **V2 with Quality Evaluator**: 
  - Inner loop: Generates each arrangement using `max_iterations`/`max_duration_sec`
  - Outer loop: Evaluates multiple arrangements up to `max_evaluation_attempts`/`max_evaluation_duration_sec`
  - Returns best scored arrangement
- **V2 with Pass-Through**: 
  - Generates one arrangement using `max_iterations`/`max_duration_sec`
  - Returns first valid arrangement (fastest overall)

### 4. Random Generator V2 (Enhanced Layered Directional Approach)

An enhanced random infill generator that improves upon the original through a layered directional approach with frame-aware anchor spacing.

**Key Improvements Over V1:**
1. **Frame-Aware Anchor Spacing**: Different minimum distances for vertical frame rods (posts) vs horizontal/sloped frame rods (handrails)
2. **Pre-Generation Strategy**: All anchor points created upfront, then distributed to layers
3. **Directional Control**: Each layer has a main direction with configurable variation
4. **Efficient Rod Creation**: Project from anchor point at target angle, find nearest anchor on opposite side
5. **Flexible Evaluation**: Works with any evaluator (Quality for optimization, Pass-Through for speed)

**V2 Generation Algorithm:**

**Phase 1: Generate Anchor Points by Frame Segment**
- Iterate through each frame rod (segment)
- Classify segment as vertical or horizontal/sloped based on dx/dy ratio (threshold: 0.1)
- Select appropriate minimum distance: `min_anchor_distance_vertical_cm` for vertical, `min_anchor_distance_other_cm` for others
- Calculate number of anchors: `segment_length / min_distance`
- Distribute anchors evenly along segment with small random offsets (±20% of min_distance)
- Use Shapely's `interpolate()` to get point coordinates
- Clean up boundary violations (remove anchors too close across segment boundaries)

**Phase 2: Distribute Anchors to Layers**
- Flatten all anchors from all segments into single list
- Randomize order using `random.shuffle()`
- Distribute to layers using round-robin: `layer = (index % num_layers) + 1`
- Result: Each layer has approximately equal number of anchors (difference ≤ 1)

**Phase 3: Calculate Layer Main Directions**
- Single layer: Use midpoint of range: `(min + max) / 2`
- Multiple layers: Linear interpolation across range
  - For layer index i: `t = i / (num_layers - 1)`
  - Main direction: `min_angle + t * (max_angle - min_angle)`
- Example with 3 layers and range [-30°, +30°]: Layer 1: -30°, Layer 2: 0°, Layer 3: +30°

**Phase 4: Generate Layer Rods**
- For each layer independently:
  1. Calculate target rod count (evenly distributed with remainder handling)
  2. Select random unused anchor as start point
  3. Calculate target angle: `main_direction + random_offset` where offset ∈ [-deviation, +deviation]
  4. Project line from start point at target angle in both directions
  5. Find intersection with frame boundary
  6. Find nearest unused anchor to intersection point on opposite side
  7. Create rod geometry connecting start and end anchors
  8. Validate constraints (length, boundary, angle, no same-layer crossings)
  9. If valid: create Rod, mark anchors as used, add to layer rods
  10. Continue until target reached or iteration/duration limit

**Phase 5: Evaluation Loop (Generator's Responsibility)**
- Quality Evaluator:
  1. Generator repeats Phases 1-4 up to `max_evaluation_attempts` times
  2. Each arrangement uses `max_iterations`/`max_duration_sec` for rod placement
  3. Evaluator scores each arrangement (evaluator just returns a number)
  4. Generator stops if `min_acceptable_fitness` reached or `max_evaluation_duration_sec` exceeded
  5. Generator returns arrangement with best fitness score
- Pass-Through Evaluator:
  1. Generator generates one arrangement (Phases 1-4)
  2. Evaluator always returns 1.0 and True (no real evaluation)
  3. Generator returns that arrangement (no loop)

**V2-Specific Parameters:**
- `min_anchor_distance_vertical_cm`: Minimum spacing for anchors on vertical frame rods (default: 15.0 cm)
- `min_anchor_distance_other_cm`: Minimum spacing for anchors on horizontal/sloped frame rods (default: 5.0 cm)
- `main_direction_range_min_deg`: Minimum angle for layer main directions (default: -30.0°)
- `main_direction_range_max_deg`: Maximum angle for layer main directions (default: +30.0°)
- `random_angle_deviation_deg`: Random deviation from layer main direction (default: 30.0°)

**Frame Segment Classification:**
- A frame rod is vertical if: `dy > 0` and `dx / dy < 0.1`
- Otherwise: horizontal/sloped
- Threshold of 0.1 means up to 10% horizontal displacement is considered "vertical"

**AnchorPoint Data Model:**
- Position (x, y coordinates)
- Frame segment index (which frame rod it's on)
- Vertical segment flag (True if on vertical frame rod)
- Assigned layer (1-N, or None if unassigned)
- Used flag (True if already used in a rod)

**Performance Characteristics:**
- Anchor generation: O(N) where N is total frame perimeter / min_distance
- Layer distribution: O(N) for shuffling and assignment
- Rod generation per layer: O(M * A) where M is target rods and A is available anchors
- Overall complexity: O(L * M * A) where L is layers, M is rods per layer, A is anchors per layer
- Memory usage: < 100 KB for typical cases

**Comparison with V1:**
- V1: Iterative random placement, single min_anchor_distance, random angles within max deviation
- V2: Directional control with layered main directions, frame-aware anchor spacing, more structured appearance
- Both: Must use an evaluator (Quality for optimization, Pass-Through for speed)
- V1 with Quality Evaluator: Iterative improvement until acceptable fitness
- V1 with Pass-Through: Returns first valid random arrangement
- V2 with Quality Evaluator: Generate N attempts, return best scored
- V2 with Pass-Through: Returns first valid directional arrangement (fastest overall)

### 5. Multi-Layer System

Rods organized into layers (rules vary by generator).

**Random Generator V1:**
- Rods within same layer cannot cross
- Rods in different layers can cross
- Default: 2 layers, each rendered in different color
- Uses selected evaluator for fitness scoring

**Random Generator V2:**
- Rods within same layer cannot cross
- Rods in different layers can cross
- Default: 2 layers, each rendered in different color
- Each layer has its own main direction
- Uses selected evaluator for fitness scoring

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

### Application State Management

The application uses a **central model pattern** with Qt's signal/slot mechanism to manage runtime state and synchronize UI components.

#### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│           RailingProjectModel (QObject)                      │
│  • Stores all runtime state (single source of truth)        │
│  • Emits signals when state changes                          │
│  • No dependencies on UI components                          │
└──────────────────────────────────────────────────────────────┘
                            ↓ signals (observer pattern)
        ┌───────────────────┼────────────────────┬─────────────┐
        ↓                   ↓                    ↓             ↓
┌───────────────┐  ┌────────────────┐  ┌──────────────┐  ┌─────────────┐
│ ViewportWidget│  │ BOMTableModel  │  │ ParameterPanel│  │ MainWindow  │
│ (observer)    │  │ (observer)     │  │ (observer)    │  │ (observer)  │
└───────────────┘  └────────────────┘  └──────────────┘  └─────────────┘
```

#### RailingProjectModel

Central state model inheriting from `QObject` for signal/slot support.

**State Storage:**
- Railing shape type and parameters
- Current RailingFrame (immutable reference)
- Generator type and parameters
- Evaluator type and parameters (required)
- Current RailingInfill (immutable reference)
- Project file path and modified flag
- UI state (enumeration visibility, etc.)

**Signals (Past Tense Naming):**
- `railing_shape_type_changed(str)` - Shape type selected
- `railing_shape_parameters_changed(object)` - Parameters modified
- `railing_frame_updated(object)` - New frame generated or cleared
- `generator_type_changed(str)` - Generator type selected
- `generator_parameters_changed(object)` - Parameters modified
- `railing_infill_updated(object)` - New infill generated or cleared
- `project_file_path_changed(object)` - File path changed
- `project_modified_changed(bool)` - Dirty flag changed
- `enumeration_visibility_changed(bool)` - Enumeration toggled

**Key Methods:**
- `set_railing_frame(frame)` - Update frame, emit signal, clear infill, mark modified
- `set_railing_infill(infill)` - Update infill, emit signal, mark modified
- `mark_project_saved()` - Clear modified flag, emit signal
- `reset_to_defaults()` - Clear all state, emit all signals

**State Dependencies:**
- Changing shape type clears RailingFrame
- Changing RailingFrame clears RailingInfill
- Any state change marks project as modified

#### Observer Pattern

UI components connect to model signals in their constructors:

```python
# ViewportWidget observes frame and infill changes
project_model.railing_frame_updated.connect(self._on_railing_frame_updated)
project_model.railing_infill_updated.connect(self._on_railing_infill_updated)

# BOMTableModel observes frame or infill (depending on table type)
project_model.railing_frame_updated.connect(self._on_railing_frame_updated)

# MainWindow observes project state for title and menu updates
project_model.project_file_path_changed.connect(self._update_window_title)
project_model.project_modified_changed.connect(self._update_window_title)
```

**Observer Responsibilities:**
- ViewportWidget: Render frame/infill geometry when signals received
- BOMTableModel: Update table data using `beginResetModel()`/`endResetModel()`
- ParameterPanel: Show/hide parameter widgets based on type changes
- MainWindow: Update title with filename and asterisk, enable/disable menu actions

#### Integration with ApplicationController

ApplicationController orchestrates workflows and updates the model:

**Workflow Pattern:**
1. Controller receives user action (e.g., "Update Shape" button clicked)
2. Controller creates domain objects (RailingShape, RailingFrame)
3. Controller updates model via setter methods
4. Model emits signals
5. UI observers receive signals and update themselves

**Example Flow:**
```
User clicks "Update Shape"
  → ApplicationController.update_railing_shape()
    → Create RailingShape instance
    → Call railing_shape.generate_frame()
    → Call project_model.set_railing_frame(frame)
      → Model emits railing_frame_updated signal
        → ViewportWidget receives signal, renders frame
        → BOMTableModel receives signal, updates table
```

**Controller Responsibilities:**
- Create domain objects (shapes, generators)
- Orchestrate background threads for generation
- Serialize/deserialize project state for save/load
- Update model, never update UI directly

#### Thread Safety

Qt signals/slots are thread-safe across thread boundaries (queued connections):

**Background Generation:**
- Generator runs in QThread
- Generator emits `progress_updated` and `generation_completed` signals
- Signals automatically queued to main thread
- ApplicationController receives signal in main thread
- Controller updates RailingProjectModel in main thread
- Model emits signals to UI observers in main thread

**Cancellation:**
- Atomic boolean flag checked by generator
- No direct thread communication needed

#### Signal Naming Conventions

**Past Tense (State Changed):**
- `railing_frame_updated` - Frame was updated
- `railing_infill_updated` - Infill was updated
- `project_modified_changed` - Modified flag changed

**Full Names:**
- Use `railing_frame_updated` not `frame_updated`
- Use `railing_infill_updated` not `infill_changed`
- Consistent with domain terminology

#### Design Rationale

**Why Central Model:**
- Single source of truth prevents state inconsistencies
- UI components don't need references to each other
- Easy to add new observers (just connect signals)
- Clear data flow: Controller → Model → Observers
- Testable (mock model, verify signals)

**Why QObject (not QAbstractItemModel):**
- QAbstractItemModel is for table/tree/list data (rows/columns)
- QObject is for application-level state
- Simpler API for non-tabular data
- BOMTableModel uses QAbstractTableModel for table data separately

### ApplicationController

Orchestrates application workflows and updates RailingProjectModel.

**Key Methods:**
- `create_new_project()` - Reset model to defaults
- `update_railing_shape(type, params)` - Generate frame, update model
- `generate_railing_infill(generator_type, generator_params, evaluator_type, evaluator_params)` - Generate infill in background with optional evaluator, update model
- `cancel_generation()` - Cancel ongoing generation
- `save_project(path)` - Serialize model state to .rig.zip
- `load_project(path)` - Deserialize and restore model state
- `export_dxf(path)` - Export current model state to DXF

**Relationship with Model:**
- Controller updates model (via setter methods)
- Model emits signals to observers
- Controller does NOT directly update UI components
- UI components observe model, not controller

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
- QComboBox for evaluator type selection (None, Quality Evaluator, future evaluators)
- QDoubleSpinBox/QSpinBox for numeric inputs with validation
- Unit suffixes displayed (cm, kg, °)
- Show/hide parameters based on selected type
- Real-time validation with inline error display
- "Update Shape" button (short operation, disables UI during execution)
- "Generate Infill" button (long operation, opens progress dialog)

**Evaluator Selection:**
- Dropdown with options: "Pass-Through (Fastest)", "Quality Evaluator", future evaluators
- Pass-Through: Returns first valid arrangement without scoring (fastest)
- Quality Evaluator: Multi-criteria fitness optimization (best quality)
- V1 with Quality Evaluator: Iterative improvement until acceptable
- V1 with Pass-Through: Returns first valid random arrangement
- V2 with Quality Evaluator: Generate multiple attempts, return best
- V2 with Pass-Through: Returns first valid directional arrangement (fastest overall)
- Evaluator parameters shown/hidden based on selection

**Evaluator Parameter Widgets:**
- `QualityEvaluatorParameterWidget`: Shows weight sliders and max hole area input
  - Max Hole Area: QDoubleSpinBox (0.1-100000.0 cm²)
  - Hole Uniformity Weight: QDoubleSpinBox (0.0-1.0)
  - Incircle Uniformity Weight: QDoubleSpinBox (0.0-1.0)
  - Angle Distribution Weight: QDoubleSpinBox (0.0-1.0)
  - Anchor Spacing Horizontal Weight: QDoubleSpinBox (0.0-1.0)
  - Anchor Spacing Vertical Weight: QDoubleSpinBox (0.0-1.0)
  - Max Evaluation Attempts: QSpinBox (1-100)
  - Max Evaluation Duration: QDoubleSpinBox (1-3600 sec)
  - Min Acceptable Fitness: QDoubleSpinBox (0.0-1.0)
  - Real-time validation: weights should sum to ~1.0
- `PassThroughEvaluatorParameterWidget`: Empty widget (no parameters)
- Pattern matches shape and generator parameter widgets

### Parameter Widget Pattern (Implemented)

All parameter widgets (shapes, generators, evaluators) follow a consistent implementation pattern:

**Base Class Structure:**
```python
class ParameterWidget(QWidget, ABC):
    """Base class for all parameter widgets"""
    
    INVALID_STYLE = "border: 2px solid #ff0000;"  # Red border for errors
    VALID_STYLE = ""
    
    def __init__(self):
        self.form_layout = QFormLayout(self)
        self.field_widgets: dict[str, QWidget] = {}  # Maps Pydantic field names to Qt widgets
        
        self._create_widgets()      # Create Qt input controls
        self._load_defaults()       # Load values from Hydra defaults
        self._connect_validation_signals()  # Connect real-time validation
    
    @abstractmethod
    def _create_widgets(self) -> None:
        """Create Qt widgets and populate field_widgets dict"""
        pass
    
    @abstractmethod
    def _load_defaults(self) -> None:
        """Load default values from dataclass into widgets"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> BaseModel:
        """Extract values and create validated Pydantic model"""
        pass
    
    def _validate_and_update_ui(self) -> None:
        """Real-time validation with visual feedback"""
        try:
            self.get_parameters()  # Attempt Pydantic validation
            self._clear_all_errors()
        except ValidationError as e:
            self._display_validation_errors(e)  # Red borders + tooltips
```

**Key Features:**
1. **field_widgets Dictionary**: Maps Pydantic field names to Qt widgets for easy access
2. **Real-Time Validation**: Connected to valueChanged signals, validates on every change
3. **Visual Feedback**: Invalid fields get red borders and error tooltips
4. **Consistent Pattern**: Same structure for shapes, generators, and evaluators
5. **Type-Safe**: Uses assert isinstance() for type narrowing before accessing widget values

**Widget Types Used:**
- `QDoubleSpinBox`: Floating-point values with range, suffix (cm, kg/m, °, sec)
- `QSpinBox`: Integer values with range, suffix (rods, layers)
- `QFormLayout`: Automatic label alignment and layout

**Validation Flow:**
1. User changes value → `valueChanged` signal emitted
2. `_validate_and_update_ui()` called
3. `get_parameters()` creates Pydantic model (may raise ValidationError)
4. If valid: Clear all error styling
5. If invalid: Red border + tooltip on invalid fields

**Example Concrete Implementation:**
```python
class StaircaseParameterWidget(ShapeParameterWidget):
    def __init__(self):
        self._defaults = StaircaseRailingShapeDefaults()  # Load from Hydra
        super().__init__()
    
    def _create_widgets(self):
        post_length_spin = QDoubleSpinBox()
        post_length_spin.setRange(1.0, 10000.0)
        post_length_spin.setSuffix(" cm")
        self.form_layout.addRow("Post Length:", post_length_spin)
        self.field_widgets["post_length_cm"] = post_length_spin  # Map to Pydantic field
        # ... create other widgets
    
    def _load_defaults(self):
        widget = self.field_widgets["post_length_cm"]
        assert isinstance(widget, QDoubleSpinBox)
        widget.setValue(self._defaults.post_length_cm)
        # ... load other defaults
    
    def get_parameters(self) -> StaircaseRailingShapeParameters:
        widget = self.field_widgets["post_length_cm"]
        assert isinstance(widget, QDoubleSpinBox)
        return StaircaseRailingShapeParameters(
            post_length_cm=widget.value(),
            # ... other parameters
        )
```

**Benefits:**
- Consistent user experience across all parameter types
- Automatic validation without manual error checking
- Easy to add new parameter widgets following the same pattern
- Type-safe with mypy validation
- Clear separation: Qt widgets → Pydantic validation → Domain objects

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
│   ├── random.yaml         # Random generator V1 defaults
│   └── random_v2.yaml      # Random generator V2 defaults
├── evaluators/
│   ├── quality.yaml        # Quality evaluator defaults
│   └── passthrough.yaml    # Pass-through evaluator defaults (empty)
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
- Generator V1 logic: arrangement generation, layer organization, constraint enforcement, Shapely operations
- Generator V2 logic: anchor point generation, frame segment classification, layer distribution, directional rod generation
- Quality evaluator: fitness calculations, individual criterion scores, hole identification using `polygonize()` (V1 only)

**Infrastructure Layer:**
- File I/O: save/load operations, ZIP structure validation, JSON schema validation
- DXF export: layer organization, entity creation, coordinate accuracy
- Configuration loading: Hydra config parsing, Pydantic validation, default value loading

### Integration Tests

**Cross-Layer:**
- Shape + Generator integration: valid arrangements for different shapes (both V1 and V2)
- Generator V1 + Evaluator integration: fitness scoring, arrangement acceptance
- Generator V2: anchor distribution, directional control, frame-aware spacing
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
- Random Generator V2 enhancements:
  - Parallel layer generation (ThreadPoolExecutor)
  - Adaptive anchor density based on segment curvature
  - Optional quality evaluation integration
  - Spatial indexing (STRtree) for faster nearest-anchor search
- Undo/redo functionality
- 3D visualization
- Material cost calculation
- Structural analysis integration
- Recent files list
- Keyboard shortcuts
- Print functionality

## Code Examples

These examples show the design patterns used across shapes, generators, and evaluators. All follow the same architecture: Hydra config → Dataclass → Pydantic → Domain object.

### Shape Pattern (Implemented)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pydantic import BaseModel, Field

# 1. Defaults (dataclass for Hydra config)
@dataclass
class StaircaseRailingShapeDefaults:
    """Loaded from conf/shapes/staircase.yaml"""
    post_length_cm: float = 150.0
    # ... other parameters

# 2. Parameters (Pydantic for UI validation)
class StaircaseRailingShapeParameters(BaseModel):
    """Runtime parameters with validation"""
    post_length_cm: float = Field(gt=0, description="Post length in cm")
    # ... other parameters
    
    @classmethod
    def from_defaults(cls, defaults: StaircaseRailingShapeDefaults):
        return cls(post_length_cm=defaults.post_length_cm, ...)

# 3. Shape interface
class RailingShape(ABC):
    """Abstract base for all shapes"""
    @abstractmethod
    def generate_frame(self) -> RailingFrame:
        """Generate frame from configuration"""
        pass

# Usage: Hydra config → Dataclass → Pydantic → Shape → Frame
```

### Generator Pattern (Implemented)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pydantic import BaseModel, Field
from PySide6.QtCore import QObject, Signal

# 1. Defaults (dataclass for Hydra config)
@dataclass
class InfillGeneratorDefaults(ABC):
    """Base class for generator defaults"""
    pass

@dataclass
class RandomGeneratorDefaults(InfillGeneratorDefaults):
    """Loaded from conf/generators/random.yaml"""
    num_rods: int = 50
    max_iterations: int = 1000
    max_duration_sec: float = 60.0
    max_evaluation_attempts: int = 10
    max_evaluation_duration_sec: float = 60.0
    min_acceptable_fitness: float = 0.7
    # ... other parameters

@dataclass
class RandomGeneratorDefaultsV2(InfillGeneratorDefaults):
    """Loaded from conf/generators/random_v2.yaml"""
    num_rods: int = 50
    min_anchor_distance_vertical_cm: float = 15.0  # V2-specific
    # ... other parameters

# 2. Parameters (Pydantic for UI validation)
class InfillGeneratorParameters(BaseModel, ABC):
    """Base class for generator parameters"""
    pass

class RandomGeneratorParameters(InfillGeneratorParameters):
    """Runtime parameters with validation"""
    num_rods: int = Field(ge=1, le=200)
    max_iterations: int = Field(ge=1, description="Max iterations per arrangement")
    max_duration_sec: float = Field(gt=0, description="Max time per arrangement")
    max_evaluation_attempts: int = Field(ge=1, description="Max arrangements to evaluate")
    max_evaluation_duration_sec: float = Field(gt=0, description="Max total evaluation time")
    min_acceptable_fitness: float = Field(ge=0, le=1, description="Min fitness to stop early")
    # ... other parameters
    
    @classmethod
    def from_defaults(cls, defaults: RandomGeneratorDefaults):
        return cls(num_rods=defaults.num_rods, ...)

class RandomGeneratorParametersV2(InfillGeneratorParameters):
    """V2 parameters with additional fields"""
    num_rods: int = Field(ge=1, le=200)
    min_anchor_distance_vertical_cm: float = Field(gt=0)  # V2-specific
    # ... other parameters
    
    @classmethod
    def from_defaults(cls, defaults: RandomGeneratorDefaultsV2):
        return cls(num_rods=defaults.num_rods, ...)

# 3. Generator interface
class Generator(QObject, ABC):
    """Abstract base for all generators"""
    PARAMETER_TYPE: type[InfillGeneratorParameters]  # Subclass defines
    
    progress_updated = Signal(dict)
    generation_completed = Signal(object)
    
    @abstractmethod
    def generate(self, frame: RailingFrame, params: InfillGeneratorParameters) -> RailingInfill:
        """Generate infill using evaluator"""
        pass

# Usage: Hydra config → Dataclass → Pydantic → Generator → Infill
```

### Evaluator Pattern (To Be Implemented)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pydantic import BaseModel, Field

# 1. Defaults (dataclass for Hydra config)
@dataclass
class QualityEvaluatorDefaults:
    """Loaded from conf/evaluators/quality.yaml"""
    max_hole_area_cm2: float = 10000.0
    hole_uniformity_weight: float = 0.3
    # ... other weights

@dataclass
class PassThroughEvaluatorDefaults:
    """Loaded from conf/evaluators/passthrough.yaml"""
    pass  # No parameters

# 2. Parameters (Pydantic for UI validation)
class QualityEvaluatorParameters(BaseModel):
    """Runtime parameters with validation"""
    max_hole_area_cm2: float = Field(gt=0)
    hole_uniformity_weight: float = Field(ge=0, le=1)
    # ... other weights
    
    @classmethod
    def from_defaults(cls, defaults: QualityEvaluatorDefaults):
        return cls(max_hole_area_cm2=defaults.max_hole_area_cm2, ...)

class PassThroughEvaluatorParameters(BaseModel):
    """No parameters"""
    pass

# 3. Evaluator interface
class Evaluator(ABC):
    """Abstract base for all evaluators"""
    
    def __init__(self, params: BaseModel):
        self.params = params
    
    @abstractmethod
    def evaluate(self, infill: RailingInfill, frame: RailingFrame) -> float:
        """Return fitness score (higher = better)"""
        pass
    
    @abstractmethod
    def is_acceptable(self, infill: RailingInfill, frame: RailingFrame) -> bool:
        """Check if arrangement meets criteria"""
        pass

# Usage: Hydra config → Dataclass → Pydantic → Evaluator → Generator
```

### Rod Model (Implemented)

```python
from pydantic import BaseModel, Field, computed_field
from shapely.geometry import LineString

class Rod(BaseModel):
    """Unified representation for frame and infill rods"""
    geometry: LineString = Field(exclude=True)
    start_cut_angle_deg: float = Field(ge=-90, le=90)
    end_cut_angle_deg: float = Field(ge=-90, le=90)
    weight_kg_m: float = Field(gt=0)
    layer: int = Field(ge=0, default=0)  # 0=frame, >=1=infill
    
    model_config = {"arbitrary_types_allowed": True}
    
    @computed_field
    @property
    def length_cm(self) -> float:
        return self.geometry.length
    
    @computed_field
    @property
    def weight_kg(self) -> float:
        return (self.length_cm / 100.0) * self.weight_kg_m
    
    def to_bom_entry(self, rod_id: int) -> dict:
        """Convert to BOM table entry"""
        return {
            "id": rod_id,
            "length_cm": round(self.length_cm, 2),
            "start_cut_angle_deg": round(self.start_cut_angle_deg, 1),
            "end_cut_angle_deg": round(self.end_cut_angle_deg, 1),
            "weight_kg": round(self.weight_kg, 3)
        }
```
