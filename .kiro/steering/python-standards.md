# Python Development Standards

This document defines the technical standards and tooling requirements for all Python development in this workspace.

## Python Version

- Use Python 3.12 for all projects
- Enforce type hints in all Python modules
- Include type stubs for all dependencies where available

## Dependency Management

- Use `uv` for all package installation and dependency management
- Maintain dependencies in `pyproject.toml`
- Generate lock files for reproducible installations
- Store virtual environments in `.venv` directory within project root

## Virtual Environment

- Create virtual environments in `.venv` directory at project root
- Use `uv run` to execute commands within the virtual environment automatically
- Exclude `.venv` from version control

## Type Checking

- Use `mypy` with strict type checking enabled
- Validate all Python files in the project
- Configure mypy through `pyproject.toml`
- Ensure type errors are reported with file locations and descriptions

## Code Quality

### Formatting and Linting
- Use `ruff` for both code formatting and linting
- Format all Python files automatically with ruff
- Check for code quality issues, style violations, and common anti-patterns
- Configure ruff through `pyproject.toml`

## Testing

- Use `pytest` as the testing framework
- Place test files in `tests/` directory
- Support fixtures and parameterized tests
- Include pytest as a development dependency
- Report test results with pass/fail status and coverage information

## Project Structure

All Python projects should follow this structure:

```
project-root/
├── src/                 # Application source code
│   └── package_name/
│       ├── __main__.py  # Entry point
│       ├── app.py       # Application setup
│       ├── domain/      # Business logic and models
│       ├── application/ # Application services
│       ├── presentation/# UI layer (if GUI app)
│       └── infrastructure/ # External services (file I/O, config)
├── tests/               # Test files
├── conf/                # Hydra configuration files
│   ├── config.yaml      # Main configuration file
│   ├── shapes/          # Config groups
│   ├── generators/
│   └── evaluator/
├── .venv/               # Virtual environment (not in git)
├── .gitignore           # Python-specific exclusions
├── pyproject.toml       # Project metadata and dependencies
└── README.md            # Project documentation
```

### Key Points:
- Use `src/` layout for application code
- Follow layered architecture: domain, application, presentation, infrastructure
- Include `tests/` directory for test files
- Store Hydra configuration files in `conf/` directory (Hydra's default)
- Main configuration file should be `conf/config.yaml`
- Organize configs with Hydra's config groups in subdirectories under `conf/`
- Exclude virtual environments, cache files (`__pycache__`, `*.pyc`), build artifacts, and Hydra outputs from version control
- Include comprehensive `.gitignore` for Python projects

## Architecture Patterns

### Layered Architecture
- **Domain Layer**: Business logic, data models (Pydantic), core algorithms
- **Application Layer**: Orchestration, workflows, state management
- **Presentation Layer**: UI components (PySide6), user interaction
- **Infrastructure Layer**: External services (file I/O, config, logging)

### Design Patterns
- **Strategy Pattern**: For interchangeable algorithms (e.g., different generators)
- **Factory Pattern**: For creating instances based on type strings
- **Observer Pattern**: Use PySide6 Signal/Slot for event handling
- **Repository Pattern**: For configuration and data access abstraction

## Geometry Operations

- Use `Shapely` for all geometry operations
- Use Shapely types: `Point`, `LineString`, `Polygon`
- Use `STRtree` for spatial indexing when needed
- Common operations:
  - `LineString.interpolate()` - Get point at distance along line
  - `LineString.intersects()` - Check if geometries intersect
  - `Point.distance()` - Calculate distance between points
  - `Polygon.area` - Calculate polygon area
  - `polygonize()` - Create polygons from line network

### Shapely with Pydantic:
```python
from pydantic import BaseModel
from shapely.geometry import LineString

class GeometryModel(BaseModel):
    geometry: LineString
    
    model_config = {"arbitrary_types_allowed": True}
```

## UI Development

- Use `PySide6` for graphical user interfaces
- Include PySide6 type stubs for type checking support
- Manage PySide6 installation through uv

### Signal/Slot Pattern

- Use PySide6's Signal/Slot mechanism for event handling and progress updates
- Prefer Signals over callbacks for type safety and thread safety
- Define typed signals (e.g., `Signal(dict)`, `Signal(object)`) for compile-time checking
- Use QThread with moveToThread pattern for background operations
- Signals automatically handle cross-thread communication safely
- Components emit signals; UI connects to slots for updates

### Threading Pattern:
```python
from PySide6.QtCore import QObject, QThread, Signal, Slot

class Worker(QObject):
    progress_updated = Signal(dict)
    finished = Signal(object)
    
    def run(self):
        # Long-running operation
        self.progress_updated.emit({"status": "working"})
        result = do_work()
        self.finished.emit(result)

# In main thread:
thread = QThread()
worker = Worker()
worker.moveToThread(thread)
thread.started.connect(worker.run)
worker.finished.connect(thread.quit)
thread.start()
```

### QGraphicsView for Vector Graphics:
- Use `QGraphicsView` and `QGraphicsScene` for 2D vector rendering
- Efficient for thousands of line items
- Built-in zoom and pan support
- Hardware-accelerated rendering

## Logging

- Use `RichHandler` from the `rich` library for console output
- Display log messages with color-coded severity levels
- Format log output with timestamps and module information
- Include `rich` as a project dependency
- Default log level should be INFO (debug logs hidden by default)
- Support debug logging via command-line argument: `-d` or `--debug`
- When debug flag is provided, set log level to DEBUG to show debug messages
- Configure logging early in application startup before other operations

## CLI Applications

- Use `Typer` for building command-line interfaces
- Implement automatic help generation with `--help` flag
- Support extensible command-line options
- Parse and validate command-line arguments
- Include Typer as a project dependency
- Always include a debug flag: `-d` / `--debug` to enable debug logging
- Debug flag should be a boolean option that controls log level (INFO by default, DEBUG when enabled)

## Naming Conventions

### Unit Suffixes for Variables and Configuration

- Always append unit suffix to variable/parameter/config names that represent physical quantities
- Use underscore separator before unit suffix
- Common unit suffixes:
  - Length: `_cm`, `_m`, `_mm`
  - Weight/Mass: `_kg`, `_g`
  - Angle: `_deg`, `_rad`
  - Time: `_sec`, `_ms`, `_min`
  - Area: `_cm2`, `_m2`
  - Speed: `_m_s`, `_km_h`
  - Weight per length: `_kg_m` (kilograms per meter)

**Examples:**
```python
# Good - unit is clear from name
post_length_cm: float = 150.0
stair_height_cm: float = 280.0
weight_per_meter_kg_m: float = 0.5
max_angle_deg: float = 30.0
max_hole_area_cm2: float = 500.0
max_duration_sec: float = 60.0

# Bad - unit is ambiguous
post_length: float = 150.0  # cm? m? mm?
weight_per_meter: float = 0.5  # kg/m? g/m?
max_angle: float = 30.0  # degrees? radians?
```

**Configuration files:**
```yaml
# conf/shapes/stair.yaml
post_length_cm: 150.0
stair_height_cm: 280.0
frame_weight_per_meter_kg_m: 0.5

# conf/generators/random.yaml
max_rod_length_cm: 200.0
max_angle_deviation_deg: 30.0
min_anchor_distance_cm: 10.0
max_duration_sec: 60.0
```

**Benefits:**
- Self-documenting code
- Prevents unit confusion errors
- No need for comments explaining units
- Type checkers can't catch unit errors, naming convention helps

## Data Validation and Models

- Use `Pydantic` for all data models and parameter validation
- Define models as `BaseModel` subclasses
- Use `@field_validator` for custom validation logic
- Use `Field()` with constraints (gt, ge, lt, le) for numeric validation
- Use `@computed_field` for derived properties
- Leverage `model_dump()` and `model_dump_json()` for serialization
- Use `model_validate()` for deserialization with validation
- Set `model_config = {"arbitrary_types_allowed": True}` when using non-Pydantic types (e.g., Shapely)

### Pydantic Field Validation Examples:
```python
from pydantic import BaseModel, Field, field_validator

class Parameters(BaseModel):
    length_cm: float = Field(gt=0)  # Must be positive
    angle_deg: float = Field(ge=-90, le=90)  # Constrained range
    count: int = Field(ge=1, le=100)  # Integer constraints
    
    @field_validator('length_cm')
    @classmethod
    def validate_length(cls, v: float) -> float:
        if v > 1000:
            raise ValueError('Length too large')
        return v
```

### Pydantic Computed Fields:
```python
from pydantic import BaseModel, computed_field

class Rod(BaseModel):
    length_cm: float
    weight_per_meter_kg_m: float
    
    @computed_field
    @property
    def weight_kg(self) -> float:
        return (self.length_cm / 100.0) * self.weight_per_meter_kg_m
```

## Configuration Management

- Use `Hydra` for hierarchical configuration management
- Store configuration files in `conf/` directory (Hydra's default location)
- Main configuration file should be `conf/config.yaml`
- Use YAML format for configuration files
- Organize related configs using Hydra's config groups (subdirectories under `conf/`)
- Use `@hydra.main()` decorator to initialize Hydra in your application
- **Integrate with Pydantic**: Load Hydra configs into Pydantic models for validation
- Support configuration composition and overrides via command line
- Include hydra-core as a project dependency

### Hydra + Pydantic Integration:
```python
import hydra
from omegaconf import DictConfig
from pydantic import BaseModel, ValidationError

class AppConfig(BaseModel):
    param1: float
    param2: int

@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig):
    try:
        # Convert Hydra config to Pydantic model for validation
        config = AppConfig(**cfg)
    except ValidationError as e:
        print(f"Invalid configuration: {e}")
        return
    
    # Use validated config
    print(config.param1)
```

### Hydra Configuration Structure:
```
conf/
├── config.yaml          # Main config file
├── db/                  # Config group for database settings
│   ├── postgres.yaml
│   └── sqlite.yaml
└── model/               # Config group for model settings
    ├── small.yaml
    └── large.yaml
```

### Configuration Override Priority (highest to lowest):
1. Command-line overrides (e.g., `python app.py db=postgres`)
2. Config group selections in main config
3. Defaults in config files

## Development Dependencies

Separate development dependencies from runtime dependencies in `pyproject.toml`:

**Runtime dependencies:**
- PySide6 (GUI framework)
- PySide6-stubs (type stubs for mypy)
- pydantic (data validation and models)
- shapely (geometry operations)
- hydra-core (configuration management)
- omegaconf (config objects)
- rich (logging)
- typer (CLI)
- ezdxf (DXF export, if needed)
- numpy (when shapely is not enough)

**Development dependencies:**
- mypy (type checking)
- ruff (formatting and linting)
- pytest (testing)
- pytest-qt (Qt testing)
- pytest-cov (coverage reporting)

## Example pyproject.toml Structure

```toml
[project]
name = "your-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "PySide6>=6.6.0",
    "PySide6-stubs",
    "pydantic>=2.0.0",
    "shapely>=2.0.0",
    "hydra-core>=1.3.0",
    "omegaconf>=2.3.0",
    "rich>=13.0.0",
    "typer>=0.9.0",
    "numpy>=1.24.0",
    "ezdxf>=1.1.0",
]

[project.optional-dependencies]
dev = [
    "mypy>=1.0.0",
    "ruff>=0.1.0",
    "pytest>=7.0.0",
    "pytest-qt>=4.0.0",
    "pytest-cov",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

## Workflow

1. Initialize project with `uv init`
2. Set up `.venv` with `uv venv`
3. Install dependencies with `uv pip install -e ".[dev]"`
4. Run type checking with `uv run mypy src/`
5. Format code with `uv run ruff format .`
6. Lint code with `uv run ruff check .`
7. Run tests with `uv run pytest`

Note: `uv run` automatically uses the project's virtual environment, so no manual activation is needed.
