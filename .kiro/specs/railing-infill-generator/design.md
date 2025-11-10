# Design Document

## Overview

The Railing Infill Generator is a desktop application that generates rod arrangements for railing frames. Users define a railing frame shape (stair or rectangular), configure generation parameters, and the application generates infill patterns using various generation algorithms. The design emphasizes extensibility, allowing new shapes and generation algorithms to be added without modifying existing code.

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

Shapes define the railing frame boundary where infill rods can be anchored.

**Shape Types:**
- **Stair Shape**: Two vertical posts + angled handrail + stepped bottom
- **Rectangular Shape**: Simple rectangular frame
- **Future**: Curved, custom polygon shapes

**Shape Interface:**
- `get_boundary()` → Shapely Polygon defining frame boundary
- `get_frame_rods()` → List of Rod objects (layer = 0)

**Parameters** (Pydantic models for UI validation):
- StairShapeParameters: post_length_cm, stair_height_cm, num_steps, frame_weight_per_meter_kg_m
- RectangularShapeParameters: width_cm, height_cm, frame_weight_per_meter_kg_m
- Initialized with defaults from Hydra config (dataclass)
- Pydantic validation errors displayed in UI

### 2. Generator System

Generators create infill rod arrangements within a shape boundary.

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
- `generate(shape, params)` → InfillResult
- Signals: `progress_updated`, `best_result_updated`, `generation_completed`, `generation_failed`

**Parameters** (Pydantic models for UI validation):
- RandomGeneratorParameters: num_rods, max_rod_length_cm, max_angle_deviation_deg, num_layers, min_anchor_distance_cm, max_iterations, max_duration_sec
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
- `rods: list[Rod]`
- `fitness_score: float | None` - Optional (for generators using evaluator)
- `iteration_count: int | None` - Optional (for iterative generators)
- `duration_sec: float | None` - Optional

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

- **Viewport**: QGraphicsView for vector rendering (zoom, pan, line rendering)
- **Parameter Panel**: Dynamic form based on selected shape/generator type
- **BOM Table**: Two tabs (Frame/Infill) with totals
- **Progress Dialog**: Shows generation progress, metrics, logs, cancel button

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

**Configuration Loading:**
- Hydra loads YAML → Dataclass (defaults)
- Dataclass → Pydantic models for UI validation
- Same Pydantic models used for UI parameter panels

### Geometry Operations (Feature-Specific)

This application uses Shapely extensively for geometric calculations:

**Common Operations:**
- `LineString.interpolate(distance)` - Get point at distance along frame for anchor points
- `LineString.intersects(other)` - Check if rods cross (same layer constraint)
- `Point.distance(other)` - Measure anchor spacing for quality evaluation
- `Polygon.area` - Calculate hole areas for quality criteria
- `polygonize(lines)` - Identify holes from rod arrangement network

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
all_lines = frame_rods + infill_rods
holes = list(polygonize([rod.geometry for rod in all_lines]))
hole_areas = [hole.area for hole in holes]
```

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

**Validation Errors:**
- Pydantic raises ValidationError with field-specific messages
- UI displays inline error feedback in parameter panel

**Generation Errors:**
- No valid arrangement found → Error message in progress dialog
- User adjusts parameters and retries

**File I/O Errors:**
- Cannot read/write files → Modal error dialog
- User chooses different location or checks permissions

## Performance Considerations


**UI Responsiveness:**
- Generator runs in QThread (moveToThread pattern)
- Signals for progress updates (max every 100ms)
- UI remains responsive during generation

## Testing Strategy

**Unit Tests:**
- Rod class (geometry, serialization, BOM)
- Shape implementations (boundary, validation, BOM)
- Generator logic (arrangement generation, layer organization)
- Quality evaluator (fitness calculations, hole identification)

**Integration Tests:**
- Shape + Generator integration
- Generator + Evaluator integration
- Application controller workflows
- End-to-end save/load cycle

**UI Tests:**
- Parameter panel updates on type selection
- Viewport rendering accuracy
- BOM table calculations
- Progress dialog behavior

## Dependencies

- PySide6 (UI framework)
- pydantic (parameter validation and data models)
- shapely (geometry operations)
- hydra-core (configuration)
- omegaconf (config objects)
- rich (logging)
- typer (CLI)
- numpy (when shapely is not enough)
- ezdxf (DXF export)

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
class StairShapeDefaults:
    """Default values loaded from Hydra YAML config (conf/shapes/stair.yaml)"""
    post_length_cm: float = 150.0
    stair_height_cm: float = 280.0
    num_steps: int = 10
    frame_weight_per_meter_kg_m: float = 0.5

@dataclass
class RectangularShapeDefaults:
    """Default values loaded from Hydra YAML config (conf/shapes/rectangular.yaml)"""
    width_cm: float = 200.0
    height_cm: float = 100.0
    frame_weight_per_meter_kg_m: float = 0.5

# Parameter models (Pydantic for UI validation)
class StairShapeParameters(BaseModel):
    """Runtime parameters with Pydantic validation for UI"""
    post_length_cm: float = Field(gt=0, description="Post length in cm")
    stair_height_cm: float = Field(gt=0, description="Stair height in cm")
    num_steps: int = Field(ge=1, le=50, description="Number of steps")
    frame_weight_per_meter_kg_m: float = Field(gt=0, description="Frame weight per meter")
    
    @field_validator('post_length_cm', 'stair_height_cm')
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Must be positive')
        return v
    
    @classmethod
    def from_defaults(cls, defaults: StairShapeDefaults) -> "StairShapeParameters":
        """Create parameters from config defaults"""
        return cls(
            post_length_cm=defaults.post_length_cm,
            stair_height_cm=defaults.stair_height_cm,
            num_steps=defaults.num_steps,
            frame_weight_per_meter_kg_m=defaults.frame_weight_per_meter_kg_m
        )

class RectangularShapeParameters(BaseModel):
    """Runtime parameters with Pydantic validation for UI"""
    width_cm: float = Field(gt=0, description="Width in cm")
    height_cm: float = Field(gt=0, description="Height in cm")
    frame_weight_per_meter_kg_m: float = Field(gt=0, description="Frame weight per meter")
    
    @classmethod
    def from_defaults(cls, defaults: RectangularShapeDefaults) -> "RectangularShapeParameters":
        """Create parameters from config defaults"""
        return cls(
            width_cm=defaults.width_cm,
            height_cm=defaults.height_cm,
            frame_weight_per_meter_kg_m=defaults.frame_weight_per_meter_kg_m
        )

class Shape(ABC):
    """Abstract base class for all railing frame shapes"""
    
    def __init__(self, params: BaseModel):  # Accepts Pydantic model
        """
        Initialize shape with validated parameters.
        Parameters are Pydantic models validated before passing here.
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
    
    def get_frame_lines(self) -> List[LineString]:
        """
        Returns frame as list of LineStrings for anchor point selection.
        Used by generators to select random anchor points along frame.
        """
        return [rod.geometry for rod in self.get_frame_rods()]

# Usage in UI:
# 1. Load defaults from Hydra config (dataclass)
# 2. Create Pydantic parameter model from defaults
# 3. User modifies in UI, Pydantic validates
# 4. Pass validated Pydantic model to Shape constructor
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
    best_result_updated = Signal(object)  # InfillResult
    generation_completed = Signal(object)  # InfillResult
    generation_failed = Signal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self._cancelled = False
    
    @abstractmethod
    def generate(self, shape: Shape, params: BaseModel) -> InfillResult:
        """
        Generate infill arrangement for the given shape.
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
