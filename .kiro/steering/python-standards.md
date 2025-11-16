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

### Testing Philosophy

**CRITICAL:** Tests must be integrated with implementation tasks, not separate.

- **Every implementation task MUST include at least one test**
- Tests should be written immediately after (or alongside) the implementation
- Never create standalone "testing tasks" - tests are part of implementation
- Follow implementation-first approach: implement feature, then write tests

### Testing Framework

- Use `pytest` as the testing framework
- Place test files in `tests/` directory mirroring `src/` structure
- Support fixtures and parameterized tests
- Include pytest as a development dependency
- Report test results with pass/fail status and coverage information

### Test Coverage Requirements

- **Unit tests**: Test individual functions, classes, and methods in isolation
- **Integration tests**: Test interactions between components
- **UI tests** (optional): Use pytest-qt for PySide6 GUI testing (can be deferred)

### Test Organization

```
tests/
├── domain/
│   ├── test_models.py
│   ├── test_shapes.py
│   └── test_generators.py
├── application/
│   └── test_controller.py
├── infrastructure/
│   └── test_logging_config.py
└── integration/
    └── test_workflows.py
```

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
├── conf/                # Hydra configuration files (if using Hydra)
│   ├── config.yaml      # Main configuration file
│   └── [feature]/       # Config groups organized by feature
├── .venv/               # Virtual environment (not in git)
├── .gitignore           # Python-specific exclusions
├── temp/                # This is for humans only, ignore in git and AI should also never ever read or update it
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

- Use `Shapely` for geometry operations when working with 2D geometric shapes
- Common Shapely types: `Point`, `LineString`, `Polygon`, `MultiPolygon`
- Use `STRtree` for spatial indexing when performing many spatial queries
- When using Shapely geometries with Pydantic, set `model_config = {"arbitrary_types_allowed": True}`

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

## Data Validation and Models

### When to Use Dataclasses vs Pydantic

**Use Dataclasses for:**
- **Configuration defaults** loaded from Hydra/YAML
- Values that work natively with Hydra's ConfigStore
- Simple data structures holding default values
- Example: `StairShapeDefaults`, `RandomGeneratorDefaults`

**Use Pydantic for:**
- **Parameter models** used in UI with real-time validation
- **Domain models** with business logic
- Models requiring computed fields (`@computed_field`)
- Models needing advanced serialization/deserialization
- Runtime data that changes during execution
- Models with complex validation logic
- Example: `StairShapeParameters`, `Rod`, `InfillResult`

**Architecture Pattern:**
```
YAML Config (Hydra) → Dataclass (defaults) → Pydantic Model (UI parameters) → Domain Logic
```

### Dataclass Configuration Defaults (for Hydra)

```python
from dataclasses import dataclass
from hydra.core.config_store import ConfigStore

@dataclass
class FeatureDefaults:
    """Default values loaded from Hydra YAML config"""
    param_one: float = 100.0
    param_two: int = 10
    weight_kg_m: float = 0.5

@dataclass
class AppConfig:
    """Main application configuration"""
    feature_defaults: FeatureDefaults

# Register with Hydra
cs = ConfigStore.instance()
cs.store(name="base_config", node=AppConfig)
cs.store(group="feature", name="default", node=FeatureDefaults)
```

### Pydantic Parameter Models (for UI)

```python
from pydantic import BaseModel, Field, field_validator, ValidationError

class FeatureParameters(BaseModel):
    """Runtime parameters with Pydantic validation for UI"""
    param_one: float = Field(gt=0, description="Parameter one")
    param_two: int = Field(ge=1, le=50, description="Parameter two")
    weight_kg_m: float = Field(gt=0, description="Weight per meter")
    
    @field_validator('param_one')
    @classmethod
    def validate_param(cls, v: float) -> float:
        if v > 1000:
            raise ValueError('Value too large')
        return v
    
    @classmethod
    def from_defaults(cls, defaults: FeatureDefaults) -> "FeatureParameters":
        """Create parameters from config defaults"""
        return cls(
            param_one=defaults.param_one,
            param_two=defaults.param_two,
            weight_kg_m=defaults.weight_kg_m
        )

# In UI code:
try:
    params = FeatureParameters(
        param_one=user_input_one,
        param_two=user_input_two,
        weight_kg_m=0.5
    )
except ValidationError as e:
    # Display validation errors in UI
    for error in e.errors():
        field = error['loc'][0]
        message = error['msg']
        # Show error message next to field in UI
```

### Pydantic Domain Models

```python
from pydantic import BaseModel, Field, computed_field

class DomainModel(BaseModel):
    """Domain model with computed fields and validation"""
    length_cm: float = Field(gt=0)
    weight_per_meter_kg_m: float = Field(gt=0)
    
    model_config = {"arbitrary_types_allowed": True}  # For Shapely types if needed
    
    @computed_field
    @property
    def weight_kg(self) -> float:
        """Computed field automatically included in serialization"""
        return (self.length_cm / 100.0) * self.weight_per_meter_kg_m
```

### Pydantic Features:
- `model_dump()` - Serialize to dictionary (includes computed fields)
- `model_dump_json()` - Serialize directly to JSON string
- `model_validate()` - Deserialize with validation
- `@computed_field` - Derived properties
- `Field()` with constraints - Numeric validation
- `@field_validator` - Custom validation logic

## Configuration Management

- Use `Hydra` for hierarchical configuration management
- Store configuration files in `conf/` directory (Hydra's default location)
- Main configuration file should be `conf/config.yaml`
- Use YAML format for configuration files
- Organize related configs using Hydra's config groups (subdirectories under `conf/`)
- Use `@hydra.main()` decorator to initialize Hydra in your application
- **Use dataclasses for Structured Configs**: Hydra works natively with dataclasses, not Pydantic
- Support configuration composition and overrides via command line
- Include hydra-core and omegaconf as project dependencies

### Hydra with Dataclass Structured Configs:
```python
from dataclasses import dataclass
import hydra
from hydra.core.config_store import ConfigStore
from omegaconf import DictConfig, MISSING, OmegaConf

@dataclass
class FeatureConfig:
    """Feature configuration parameters"""
    param_one: str = "default"
    param_two: int = 100
    
    def __post_init__(self):
        """Validate after initialization"""
        if self.param_two < 1:
            raise ValueError("param_two must be positive")

@dataclass
class AppConfig:
    """Main application configuration"""
    feature: FeatureConfig = MISSING
    debug: bool = False

# Register structured configs with Hydra
cs = ConfigStore.instance()
cs.store(name="base_config", node=AppConfig)
cs.store(group="feature", name="default", node=FeatureConfig)

@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: AppConfig):  # Type hint with dataclass
    # Hydra automatically validates against dataclass schema
    # cfg is a DictConfig but validated against AppConfig structure
    print(f"Feature param: {cfg.feature.param_one}")
    
    # Convert to dataclass instance if needed
    config_obj = OmegaConf.to_object(cfg)  # Returns AppConfig instance
    print(config_obj.feature.param_one)

if __name__ == "__main__":
    main()
```

### Hydra Configuration Structure:
```
conf/
├── config.yaml          # Main config file
└── feature/             # Config group for feature settings
    ├── option_a.yaml
    └── option_b.yaml
```

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

### Initial Setup

1. Initialize project with `uv init`
2. Set up `.venv` with `uv venv`
3. Install dependencies with `uv pip install -e ".[dev]"`

### Task Workflow (Before Starting and After Completing Each Task)

**CRITICAL:** Follow this workflow for every task:

#### Before Starting a Task:

1. **Record baseline coverage**:
   ```bash
   uv run pytest --cov=railing_generator --cov-report=term-missing
   ```
   - Note the **TOTAL coverage percentage** (e.g., "51%")
   - Add this as a note to the task: "Starting coverage: 51%"
   - This is your baseline to maintain or improve

#### During Development:

Run these checks after every code change:

1. **Type checking**: `uv run mypy src/`
   - Ensures type correctness and catches type errors early
   - Must pass with no errors before proceeding

2. **Linting**: `uv run ruff check .`
   - Checks code quality, style violations, and common anti-patterns
   - Must pass with no errors before proceeding

3. **Formatting**: `uv run ruff format .`
   - Automatically formats code to consistent style
   - Run before committing code

4. **Testing with coverage**: `uv run pytest --cov=railing_generator --cov-report=term-missing`
   - Runs all tests to verify functionality
   - Shows coverage report with missing lines
   - Check that coverage is maintained or improved

#### Before Completing a Task:

1. **Verify coverage requirement**:
   - Run: `uv run pytest --cov=railing_generator --cov-report=term-missing`
   - Check the **TOTAL coverage percentage**
   - **REQUIREMENT**: New coverage MUST be >= baseline coverage
   - If coverage dropped, add more tests to cover the new code
   - Add final coverage as note: "Ending coverage: 55%"

2. **All checks must pass**:
   - ✅ mypy: No type errors
   - ✅ ruff: No linting issues
   - ✅ pytest: All tests passing
   - ✅ coverage: >= baseline coverage

**Example Task Notes:**
```
Task 2.1: Implement Rod class
- Starting coverage: 51%
- Ending coverage: 58% ✅ (improved)
```

### Quick Check Command

Run all checks in sequence:
```bash
uv run mypy src/ && uv run ruff check . && uv run pytest --cov=railing_generator --cov-report=term-missing
```

### Coverage Report

After running tests with coverage, you'll see:
- Overall coverage percentage
- Per-file coverage
- Line numbers that are not covered (missing)
- Use this to identify untested code paths

Note: `uv run` automatically uses the project's virtual environment, so no manual activation is needed.
