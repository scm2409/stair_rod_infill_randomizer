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

See the steering document for detailed patterns and examples.

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

**Parameters** (Pydantic models with validation):
- StairShapeParameters: post_length_cm, stair_height_cm, num_steps, frame_weight_kg_m
- RectangularShapeParameters: width_cm, height_cm, frame_weight_kg_m

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

**Parameters** (Pydantic models with validation):
- RandomGeneratorParameters: num_rods, max_rod_length_cm, max_angle_deviation_deg, num_layers, min_anchor_distance_cm, max_iterations, max_duration_sec

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

```
┌─────────────────────────────────────────────────────────────┐
│  Menu Bar: File | View | Help                               │
├──────────────┬──────────────────────────────────────────────┤
│  Parameter   │      Viewport (zoom, pan, render)            │
│  Panel       │                                              │
│  - Shape     ├──────────────────────────────────────────────┤
│  - Generator │  BOM Table (2 tabs: Frame | Infill)         │
│  - Buttons   │  - ID, Length, Start Angle, End Angle, Weight│
├──────────────┴──────────────────────────────────────────────┤
│  Status Bar: Ready | File: project.rig.zip* | Rods: 50      │
└─────────────────────────────────────────────────────────────┘
```

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
- Hydra loads YAML → dict
- Dict passed to Pydantic models for validation
- Same models used for UI parameter panels

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
User clicks "Update Shape" → Validate parameters (Pydantic) →
Create shape instance → Viewport renders frame → BOM table updates
```

### Infill Generation Flow

```
User configures generator → User clicks "Generate Infill" →
Validate parameters (Pydantic) → Progress dialog opens →
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
  - Serialize parameters (Pydantic model_dump_json)
  - Serialize infill geometry (Pydantic model_dump_json)
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

### Shape Interface

```python
from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel, field_validator, Field
from shapely.geometry import Polygon

class ShapeParameters(BaseModel):
    """Base class for shape parameters"""
    pass

class StairShapeParameters(ShapeParameters):
    post_length_cm: float = Field(gt=0)
    stair_height_cm: float = Field(gt=0)
    num_steps: int = Field(ge=1, le=50)
    frame_weight_kg_m: float = Field(gt=0)

class Shape(ABC):
    def __init__(self, params: ShapeParameters):
        self.params = params
    
    @abstractmethod
    def get_boundary(self) -> Polygon:
        pass
    
    @abstractmethod
    def get_frame_rods(self) -> List[Rod]:
        pass
```

### Generator Interface

```python
from abc import ABC, abstractmethod
from PySide6.QtCore import QObject, Signal

class Generator(QObject, ABC):
    progress_updated = Signal(dict)
    best_result_updated = Signal(object)
    generation_completed = Signal(object)
    generation_failed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._cancelled = False
    
    @abstractmethod
    def generate(self, shape: Shape, params: GeneratorParameters) -> InfillResult:
        pass
    
    def cancel(self):
        self._cancelled = True
```

### Rod Class

```python
from pydantic import BaseModel, Field, computed_field
from shapely.geometry import LineString, Point

class Rod(BaseModel):
    geometry: LineString = Field(exclude=True)
    start_cut_angle_deg: float = Field(ge=-90, le=90)
    end_cut_angle_deg: float = Field(ge=-90, le=90)
    weight_kg_m: float = Field(gt=0)
    layer: int = Field(ge=0, default=0)
    
    model_config = {"arbitrary_types_allowed": True}
    
    @computed_field
    @property
    def length_cm(self) -> float:
        return self.geometry.length
    
    @computed_field
    @property
    def weight_kg(self) -> float:
        return (self.length_cm / 100.0) * self.weight_kg_m
```
